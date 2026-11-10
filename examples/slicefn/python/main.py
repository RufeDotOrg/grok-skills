# run the functions stored in demo.slicefn
import importlib.machinery, importlib.util
loader = importlib.machinery.SourceFileLoader("demo", "demo.slicefn")
spec = importlib.util.spec_from_loader("demo", loader)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)

print(demo.greet("slicefn"))
print(demo.fib(20))
