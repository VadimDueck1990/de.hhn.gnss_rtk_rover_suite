import micropython
import gc


def debug_gc():
    """
    Simple helper function which garbage collects and prints the memory info before and after to the screen
    """
    print("================================================================")
    micropython.mem_info()
    gc.collect()
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ")
    micropython.mem_info()
    print("================================================================")
