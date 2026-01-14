str1="python est simple"
print(str1[3])
print(str1[-3])
""" les objets str sont non modifiables
 str1[0]='C'
print(str1) """
#acces à une plage de caractères
print(str1[1:5:2])
print(str1[0:6:1])
# ou print(str1[:6])
print(str1[-1:-4:-1])
print(str1[::-1])
#upper
str1.upper()
print(str1)

