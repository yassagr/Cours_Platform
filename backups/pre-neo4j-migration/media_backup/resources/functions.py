# Simple function without 
def sayHello():
    print("hello")

sayHello()
# Function with one parameter
def sayHello(name):
    print(" hello ", name)
    
sayHello("ali")
# Function with multiple parameters and return value
def addition(num1, num2):
    return num1+num2

somme=addition(2,5)
print(somme)
# Function with a default parameter value
def sayHello(name="unknown"):
    print("hello ",name)
    
sayHello()
# Function with *args (variable number of arguments)
def addition(*numbers):
    print(type(numbers))
    return sum(numbers)

somme=addition(1,2,3,4)
print(somme)
# Function with **kwargs (named arguments)
def person_infos(**x):
    print(x)
    for key, value in x.items():
        print(key , ":" , value)

person_infos(name="ali", age=22)

# passage par adresse

myList=[1,3,9]

def modifierList(list):
    list.append(2)

modifierList(myList)
print(myList)
    