# Creating a list of elements
cities=["rabat","paris","tangier"]
# Displaying the complete list
print("list : ",cities)
# Accessing elements
print("the first element is :", cities[0])
print("the last element is:", cities[-1])
# Modifying an element
cities[1]="casablanca"
print(cities)
# Adding an element to the end
cities.append("tokyo")
print(cities)
# Inserting an element at a specific index
cities.insert(2,"paris")
print(cities)
# Adding multiple elements
cities.extend(["agadir","paris"])
print(cities)
# Removing an element by value
cities.remove("paris")
print(cities)
# Removing an element by index
cities.pop(3)
print(cities)
# Sorting the list in alphabetical order
cities.sort()
print(cities)
# Sorting the list in reverse order
cities.sort(reverse=True)
print(cities)
# Checking if an element is in the list
if "rabat" in cities:
    print("it exists")
# Getting the total number of elements in the list
print("the length is ",len(cities))
# Looping through the list
for city in cities:
    print(city)
# Creating a list of numerical values and applying a transformation (list comprehension)
numbers=[2,7,8,4]
number_to_power_2=[ i**2 for i in numbers]
print(number_to_power_2)
# Copying a list
names=["ali", "amine", "anas"]
names1=names.copy()
names1.append("ahmed")
print(id(names))
print(id(names1))
print(names)
# Clearing the list
cities.clear()
print(cities)

del cities
print(id(cities))

