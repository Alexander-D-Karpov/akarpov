import cProfile
import os
import pstats

import django


# Function to run the Django setup process, which you want to profile
def django_setup():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()


# Create a Profile object and run the django_setup function
profiler = cProfile.Profile()
profiler.enable()
django_setup()
profiler.disable()

# Write the stats to a .prof file
profiler.dump_stats("django_setup.prof")

# Create a Stats object and print the sorted stats to a text file
with open("django_setup.txt", "w") as stream:
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumtime")  # Sort the statistics by cumulative time
    stats.print_stats()  # Print the statistics to the stream

# Optionally, print the stats to the console as well
stats = pstats.Stats(profiler)
stats.sort_stats("cumtime")
stats.print_stats()
