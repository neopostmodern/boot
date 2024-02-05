"""This script is only used to create nicer REPL session to test hardware functions"""

from client.hardware import Hardware

h = Hardware()
print()
print("Hardware is available as 'h':")
for prop in dir(h):
    if prop.startswith("__"):
        continue
    print(f"    h.{prop}")
print()
print(f"PSU is {'on' if h.psu.is_on() else 'off'}")
