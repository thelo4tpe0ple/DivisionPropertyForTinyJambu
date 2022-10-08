from gurobipy import *

FrameBitsIV=0x1
FrameBitsAD=0x3
FrameBitsPC=0x5

def And(m,in1,in2,out):
	# m.addConstr(out == in1)
	# m.addConstr(out == in2)
	m.addConstr(out >= in1)
	m.addConstr(out >= in2)
	m.addConstr(out - in1 - in2 <= 0)
	return m

def Xor(m,in1,in2,out):
	m.addConstr(in1 + in2 == out )
	return m

def Copy(m,inv,outv1,outv2):
	m.addConstr(inv == outv1 + outv2)
	# m.addConstr(outv1 + outv2 >= inv)
	# m.addConstr(inv >= outv1)
	# m.addConstr(inv >= outv2)
	return m

def TinyJambuCore(model,S,i1=0,i2=47,i3=70,i4=85,i5=91,ik=128):
	y1=model.addVar(0,1,0,GRB.BINARY)
	y2=model.addVar(0,1,0,GRB.BINARY)
	y3=model.addVar(0,1,0,GRB.BINARY)
	y4=model.addVar(0,1,0,GRB.BINARY)
	y5=model.addVar(0,1,0,GRB.BINARY)
	y6=model.addVar(0,1,0,GRB.BINARY)
	#y7=model.addVar(0,1,0,GRB.BINARY)
	#z1=model.addVar(0,1,0,GRB.BINARY)
	z2=model.addVar(0,1,0,GRB.BINARY)
	z3=model.addVar(0,1,0,GRB.BINARY)
	z4=model.addVar(0,1,0,GRB.BINARY)
	z5=model.addVar(0,1,0,GRB.BINARY)
	z6=model.addVar(0,1,0,GRB.BINARY)
	a=model.addVar(0,1,0,GRB.BINARY)
	 #model.update()
	#0bit
	#Operation.Copy(model,S[i1],y1,z1)
	#47bit
	Copy(model,S[i2],y2,z2)
	#70bit
	Copy(model,S[i3],y3,z3)
	#85bit
	Copy(model,S[i4],y4,z4)
	#91bit
	Copy(model,S[i5],y5,z5)
	#K bit
	Copy(model,S[ik],y6,z6)

	# model.addConstr(a >= z3)
	# model.addConstr(a >= z4)
	And(model,z3,z4,a)
	model.addConstr(y1 == z6 + a + S[i1] + z2 + z5)

	S[i1] = y1
	S[i2] = y2
	S[i3] = y3
	S[i4] = y4
	S[i5] = y5
	S[ik] = y6
	#return S[32:63]






def TinyJambuEval(I1,I2,round3):
	model=Model()
	#s[0:127] -- state
	#s[128:255] -- key
	#nonce[64:95] -- cube
	s = [model.addVar(0,1,0,GRB.BINARY) for i in range(256)]
	work = [model.addVar(0,1,0,GRB.BINARY) for i in range(256)]
	temp1 = [model.addVar(0,1,0,GRB.BINARY) for i in range(128)]
	temp2 = [model.addVar(0,1,0,GRB.BINARY) for i in range(128)]
	nonce = [model.addVar(0,1,0,GRB.BINARY)for i in range(96)]
	plaintext = [model.addVar(0,1,0,GRB.BINARY)for i in range(128)]

	# model.update()
	# print("plaintext: ",plaintext)
	#set cube
	for i in range(96):
		if i in I1:
			model.addConstr(nonce[i] == 1)
		else:
			model.addConstr(nonce[i] == 0)
			
	for i in range(128):
		if i in I2:
			model.addConstr(plaintext[i] == 1)
		else:
			model.addConstr(plaintext[i] == 0)
	J=[]
	
	
	#model.update()
	#print("nonce: ",nonce)
	#set state and key 
	for i in range(128):
		model.addConstr(s[i] == 0)


	model.addConstr(quicksum(s[128:255]) == 1)

	for i in range(256):
		work[i] = s[i]

	

	#Key Setup
	for i in range(1024):
		TinyJambuCore(model,work)
		#update state
		for j in range(128):
			temp1[j] = work[j]
			temp2[j] = work[j+128]
		for j in range(128):
			work[j] = temp1[(j + 1)%128]
			work[j+128] = temp2[(j + 1)%128]
	#model.update()

	#nonce setup
	for i in range(3):

		for j in range(384):

			TinyJambuCore(model,work)

			for k in range(128):
				temp1[k] = work[k]
				temp2[k] = work[k+128]

			for k in range(128):
				work[k] = temp1[(k + 1)%128]
				work[k+128] = temp2[(k + 1)%128]
	
		#print(f"work in {i} :" ,work)
		y1 = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]
		y2 = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]
		z = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]
		for j in range(32):
			Copy(model,nonce[i*32+j],y1[j],y2[j])


		for j in range(32):
			model.addConstr(z[j] == work[j+96] + y1[j])
			work[j+96] = z[j]

	
	for r in range(len(plaintext)//32):
		for i in range(round3):
			TinyJambuCore(model,work)
			for j in range(128):
				temp1[j] = work[j]
				temp2[j] = work[j+128]
			for j in range(128):
				work[j] = temp1[(j+1)%128]
				work[128+j] = temp2[(j+1)%128]

		
		y1 = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]
		y2 = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]
		z = [model.addVar(0,1,0,GRB.BINARY) for i in range(32)]

		for i in range(32):
			Copy(model,plaintext[i+r*32],y1[i],y2[i])

		for i in range(32):
			model.addConstr(z[i] == work[96+i] + y1[i])

			work[j+96] = z[i]

		nk = 0
		for i in range(256):
			if i >= 64 and i <= 95:
				nk += work[i]
			else:
				model.addConstr(work[i] == 0)
		model.addConstr(nk == 1)

	
	
	
	model.update()
	
	while True:
			model.optimize()
			if model.status == 2:
				for idx in range(128):
					if s[idx+128].Xn == 1:
						J.append(idx)
						model.addConstr(s[idx+128] == 0 )
			elif model.status == 3:
				model.computeIIS()
				model.write("error.ilp")
				break
	return J


# def gurobiImpos(model):
# 	model_flag=1
# 	model.optimize()
# 	if model.status == 2: #feasible
# 		model_flag = 1
# 	if model.status == 3: #infeasible
# 		model_flag = 0
# 	return model_flag 

if __name__ == '__main__':
	
	I1=[8,23,25,31,35,36,39,40,54,56,57,65,68,71,72,73,74,76,78,83,84,87,90,93,94]	
	I2=[i for i in range(128) if i%2==1]#360rounds


	#I1=[64,69,70,71,76,81,86,91,92] #	153 rounds
	
	#I1=[64,65,67,69,70,71,72,74,76,78,79,80,81,83,84,85,86,88,90,91,94]#188 rounds
	#I=[64,66,67,68,72,73,75,77,79,81,82,83,84,87,88,89,90,91,92,93,94]#	186 rounds

	
	#I=[0,27,30,46,52,58,60,61,63]
	#I=[8,23,25,31,35,36,39,40,54,56,57,65,68,71,72,73,74,76,78,83,84,87,90,93,94]
	#I=[1,44,60,61]
	#I=[81,86,91,92]
	#I=[3,8,21,28,36,37,53,60,63,65,72,82,84,88,93]
	
	
	J=TinyJambuEval(I1,I2,100)
	
	print(J)
	if len(J)<128:
		for i in range(128):
			if i not in J:
				print(i)

			
	#J=attackFramework(model,I)
	
	