import pybuildsys
import multiprocessing

@pybuildsys.target()
def print_hello_target():
    yield pybuildsys.shell("echo", "Hello,")

@pybuildsys.target()
def print_world_target():
    yield pybuildsys.shell("echo", "World!")

@pybuildsys.target()
def print_hello_world():
    yield print_hello_target()
    yield pybuildsys.Barrier()
    yield print_world_target()

if __name__ == "__main__":
    pybuildsys.execute(print_hello_world(), jobs=multiprocessing.cpu_count())
