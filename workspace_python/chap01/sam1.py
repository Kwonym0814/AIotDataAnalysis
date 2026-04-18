print("덧셈 : ",100+200)
print("뺄셈 : ",100-200)
print("곱셈 : ",100*200)
print("나눗셈 : ",100/200)
print("나머지 : ",100%200)

'''
실행결과
덧셈 :  300
뺄셈 :  -100
곱셈 :  20000
나눗셈 :  0.5
나머지 :  100
'''
print(1<10, 1>10, 1<=10, 1>=10, 1==10, 1!=10)
# 실행결과 True False True False False True

print(1==1 and 2==2)
print(1==1 or 2==2)
print(not(1==1))
'''
True
True
False
'''

a=100
b=10
a+=b # a = a + b
print(a, b)
a-=b # a=a-b
print(a, b)
a*=b #a=a*b
print(a, b)
a/=b #a=a/b
print(a, b)

a=100
b=1.5
c=True
d="Hello"
print(type(a))
print(type(b))
print(type(c))
print(type(d))
'''
실행결과
<class 'int'>
<class 'float'>
<class 'bool'>
<class 'str'>
'''