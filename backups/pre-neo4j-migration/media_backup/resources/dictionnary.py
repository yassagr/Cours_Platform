# Creating a simple dictionary
person={
    "name":"ali",
    "age":22,
    "country":"morocco"
}
# Displaying the complete dictionary
print(type(person))
# Accessing values by key
print(person["age"])
# Modifying a value
person["country"]="spain"
print(person)
# Adding a new key-value pair
person["job"]="data scientist"
print(person)
# Removing and retrieving a value using `pop`
country_deleted=person.pop("country")
print(country_deleted)
print(person)
# Checking if a key exists
if "country" in person:
    print("yes it exists")
else:
    print("no it deos not")
# Getting the length of the dictionary
print(len(person))
# Iterating through keys
for key in person.keys():
    print(key)
# Iterating through values
for value in person.values():
    print(value)
# Iterating through key-value pairs
for key, value in person.items():
    print(key , " : " , value)
    
print(person.keys())
print(person.values())
print(person.items())
# Copying a dictionary
new_person=person.copy()
# Clearing the dictionary
person.clear()
