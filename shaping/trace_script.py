res = ""
a = 0




#6mbits
#for i in range(500):
#	a = a+2
#	res += str(a)+"\n"

#4mbits
#for i in range(333):
#	a = a+3
#	res += str(a)+"\n"

#2mbits
#for i in range(166):
#	a = a+6
#	res += str(a)+"\n"

#360mbits
res+= "1\n"*30

with open("jiamo.trace.txt", 'a') as out:
    out.write(res)



