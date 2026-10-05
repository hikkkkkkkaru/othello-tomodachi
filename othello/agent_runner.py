"""ファイルからエージェントを読み込み、別プロセスで実行する。"""
import importlib.util
import multiprocessing as mp
import traceback
from pathlib import Path

from othello.engine import MOVE_TIMEOUT


def load_agent(path):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    classes = [obj for obj in vars(mod).values()
               if isinstance(obj, type) and obj.__module__ == mod.__name__
               and hasattr(obj, "select_action")]
    if len(classes) != 1:
        raise ValueError(f"{path}: select_action を持つクラスを1つ定義してください")
    return classes[0]()


def _worker(path, connection):
    try:
        agent = load_agent(path)
        connection.send((True, None))
        while True:
            board, player = connection.recv()
            try:
                connection.send((True, agent.select_action(board, player)))
            except Exception:
                connection.send((False, traceback.format_exc()))
    except EOFError:
        pass
    except Exception:
        connection.send((False, traceback.format_exc()))
    finally:
        connection.close()


class ProcessAgent:
    """1試合中は状態を保持する。制限超過時はプロセスを終了する。"""
    def __init__(self, path, timeout=MOVE_TIMEOUT):
        self.path = Path(path)
        self.timeout = timeout
        self.process = None
        self.connection = None

    def __enter__(self):
        ctx = mp.get_context("spawn")
        self.connection, child = ctx.Pipe()
        self.process = ctx.Process(target=_worker, args=(self.path, child), daemon=True)
        self.process.start()
        child.close()
        try:
            self._receive(60.0)  # 起動・import は着手時間と分ける
        except BaseException:
            self.close()
            raise
        return self

    def _receive(self, timeout):
        if not self.connection.poll(timeout):
            self.close()
            raise TimeoutError(f"{self.path.name}: 制限時間 {timeout} 秒を超過")
        try:
            ok, result = self.connection.recv()
        except EOFError as exc:
            raise RuntimeError(f"{self.path.name}: エージェントが終了しました") from exc
        if not ok:
            raise RuntimeError(f"{self.path.name}:\n{result}")
        return result

    def select_action(self, board, player):
        if self.process is None or not self.process.is_alive():
            raise RuntimeError(f"{self.path.name}: 実行プロセスが停止しています")
        self.connection.send((board, player))
        return self._receive(self.timeout)

    def close(self):
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
        if self.connection is not None:
            self.connection.close()

    def __exit__(self, *args):
        self.close()
