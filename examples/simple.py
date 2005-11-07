import seppo
import example_module

results = seppo.map_parallel(example_module.hello_world, [1,2,3,4,5])

for result in results:
    print result
