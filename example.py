import pybuildsys
import multiprocessing

def print_hello1():
    hello_printed = False

    def on_hello():
        nonlocal hello_printed
        hello_printed = True

    yield pybuildsys.build.shell("echo", f"1: World!", silent=True).depends_on(lambda: hello_printed)
    yield pybuildsys.build.shell("echo", f"1: Hello!", silent=True).on_finish(on_hello)

def print_hello2():
    yield pybuildsys.build.shell("echo", f"2: Hello!", silent=True).on_finish(
        lambda: pybuildsys.build.shell("echo", f"2: World!", silent=True))

def build_project():
    yield from print_hello1()
    yield from print_hello2()

if __name__ == "__main__":
    pybuildsys.execute(build_project(), jobs=multiprocessing.cpu_count())
