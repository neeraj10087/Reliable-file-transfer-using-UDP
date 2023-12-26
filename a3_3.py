import socket
import time
import hashlib
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host="127.0.0.1"
port = 9802
sock.settimeout(0.01)
start = time.time()
msg0 = "SendSize\nReset\n\n"
while True:
    sock.sendto(msg0.encode(),(host,port))
    sent_time = time.time()
    try:
        data,addr = sock.recvfrom(4096)
        data = data.decode()
        recv_time = time.time()
        print(data)
        Size = int(data.split(": ")[1].strip("\n\n"))
        break
    except socket.timeout:
        print("size not recieved")
first_rtt = recv_time - sent_time
a = first_rtt
nors = Size//1448
if Size%1448 != 0:
    nors += 1
requests = [i*1448 for i in range(nors)]
result = ["" for i in range(nors)]
errors = 0
sent_times =[0 for i in range(nors)]
rec_times =[0 for i in range(nors)]
burst_sent = 3
squishes =0
while len(requests)>0:
    requests_sent =[]
    sent_size =0
    skips = 0
    in_squish = 0
    for i in range(burst_sent):
        if len(requests)>0:
            offset = requests.pop(0)
            if Size-offset >=1448:
                req = "Offset: "+str(offset)+"\nNumBytes: 1448\n\n"
            else:
                req = "Offset: "+str(offset)+"\nNumBytes: "+str(Size%1448)+"\n\n"
            sock.sendto(req.encode(),(host,port))
            requests_sent.append(offset)
            sent_times[offset//1448] = time.time()
            sent_size += 1
            # time.sleep(a/burst_sent)
    burst_recv = sent_size
    time.sleep(a)
    for i in range(burst_recv):
        try:
            data,addr = sock.recvfrom(4096)
            data = data.decode()
            recv_time = time.time()
            p = data.split("\n\n")
            p1 = p[0]
            p2 = p[1]
            p1 = p1.split("\n")
            offset = int(p1[0].split("Offset: ")[1])
            print("offset:",offset)
            if len(p1) == 3:
                print("squish")
                # time.sleep(1)
                squishes += 1
                in_squish += 1
            result[offset//1448] = p2
            rec_times[offset//1448] = recv_time
        except socket.timeout:
            print("timeout")
            continue
    b = 0.03
    c=0
    if in_squish >1:
        time.sleep(1)
    for r in requests_sent:
        if result[r//1448] == "":
            requests.append(r)
            skips += 1
        else:
            t = rec_times[r//1448] - sent_times[r//1448]
            c = max(c,t)
            if t >0:
                b = min(b,t)
    if skips <= 1 and in_squish == 0:
        burst_sent += 1
    elif skips >1 or in_squish >0:
        burst_sent = max(burst_sent//2,1)
    a = a*0.2 + b*0.8
    a = min(a,0.0236)
    # print("b:",b)
    # print("a:",a)
    # sock.settimeout(b)
################# loop ends ############################
print("squishes:",squishes)
ans =""
for i in range(len(result)):
    if result[i] == "":
        errors += 1
    else:
        ans += result[i]
print("errors:",errors)
print("requests:",nors)
result_md5 = hashlib.md5(ans.encode()).hexdigest()
print("MD5 hash: ",result_md5)
msg_s ="Submit: [cs1210087@team]\n"+"MD5: "+str(result_md5)+"\n\n"
while True:
    sock.sendto(msg_s.encode(),(host,port))
    try:
        submit,addr = sock.recvfrom(4096)
        submit = submit.decode()
        su = submit.split("\n")
        if len(su) == 5:
            print(submit)
            break
    except socket.timeout:
        print("Timeout")
print("first_rtt:",first_rtt)
#final