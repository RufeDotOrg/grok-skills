# run the functions stored in demo.slicefn.py
import importlib.util
spec = importlib.util.spec_from_file_location("demo", "demo.slicefn.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)

print(demo.greet("slicefn"))
print(demo.fib(20))
