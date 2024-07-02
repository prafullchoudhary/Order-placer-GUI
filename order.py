import tkinter as tk
from tkinter import ttk
from tkinter import *
import datetime
from datetime import datetime
import time
from smartapi import SmartConnect
import pandas as pd
import requests
import concurrent.futures
from functools import partial

USER_NAME = ''
PWD = ''
API_KEY = ''


with concurrent.futures.ThreadPoolExecutor() as executor:
    win = tk.Tk()
    win.title("Order Placer For Nifty/BankNifty")
    win.geometry("320x240")
    win.rowconfigure(0, weight=8)
    win.columnconfigure(0, weight=1)
    win1 = tk.Frame(win)
    win2 = tk.Frame(win)
    win3 = tk.Frame(win)
    win0 = tk.LabelFrame(win2)
    win0.pack(fill=X)
    for frame in (win1, win2, win3):
        frame.grid(row=0,column=0,sticky='nsew')

    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    d = requests.get(url).json()
    global token_df
    token_df = pd.DataFrame.from_dict(d)
    print(token_df['expiry'].head())
    token_df['expiry'] = pd.to_datetime(token_df['expiry'])
    print(token_df['expiry'].head())
    token_df = token_df.astype({'strike': float})
    token_df = token_df[(token_df['exch_seg'] == 'NFO') & (token_df['instrumenttype'] == 'OPTIDX') & ((token_df['name'] == 'BANKNIFTY') | (token_df['name'] == 'NIFTY'))].sort_values(by=['expiry'])
    token_df['strike'] = token_df['strike']/100
    token_df = token_df[token_df['expiry'].dt.date>=datetime.today().date()]
    
    obj=SmartConnect(API_KEY)
    data = obj.generateSession(USER_NAME,PWD)
    refreshToken= data['data']['refreshToken']
    feedToken=obj.getfeedToken()

    basket={}
    square={}
    sl_tp={}
    ki=0
    sp=0
    c=0
    idnt=''
    ism=0

    def show_frame(frame):
        frame.tkraise()

    def place_order(symbol,token,buy_sell,producttype,qty,ordertype,price):
        try:
            obj.placeOrder({
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": buy_sell,
                "exchange": "NFO",
                "ordertype": ordertype,
                "producttype": producttype,
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": qty
                })
        except Exception as e:
            print(f"Order placement failed: {e}")

    def convert(old,new,symbol,tpe,qty):
        try:
            obj.convertPosition({
            "exchange": "NFO",
            "oldproducttype":old,
            "newproducttype": new,
            "tradingsymbol": symbol,
            "transactiontype":tpe,
            "quantity":qty,
            "type":"DAY"
            })
        except Exception as e:
            print(f"Conversion failed: {e}")

    def Position():
        p=obj.position()
        if p['status']==True and p['data']!=None:
            square.clear()
            pos=0
            for i in p['data']:
                if int(i["netqty"])>0 or int(i["netqty"])<0:
                    if int(i["netqty"])>0:
                        if int(i["lotsize"])==25:
                            square[pos]=[i["tradingsymbol"],i["symboltoken"],int(i["netqty"]),'BUY',i["producttype"],1200,"MARKET",'0']
                        if int(i["lotsize"])==50:
                            square[pos]=[i["tradingsymbol"],i["symboltoken"],int(i["netqty"]),'BUY',i["producttype"],1800,"MARKET",'0']
                    if int(i["netqty"])<0:
                        if int(i["lotsize"])==25:
                            square[pos]=[i["tradingsymbol"],i["symboltoken"],(int(i["netqty"])*-1),'SELL',i["producttype"],1200,"MARKET",'0']
                        if int(i["lotsize"])==50:
                            square[pos]=[i["tradingsymbol"],i["symboltoken"],(int(i["netqty"])*-1),'SELL',i["producttype"],1800,"MARKET",'0']
                    square[pos].append(tk.IntVar())
                    square[pos].append(ttk.Checkbutton(win4,variable=square[pos][8]))
                    square[pos][9].grid(row=pos, column=0, pady=15, padx=5)
                    ttk.Label(win4, text=square[pos][0],font= ('Goudy old style', 10)).place(x=25,y=((51*pos)+5))
                    ttk.Label(win4, text=f'QTY. {square[pos][2]}',font= ('Goudy old style', 10)).place(x=220,y=((51*pos)+5))
                    ttk.Label(win4, text=f'{square[pos][3]} |',font= ('Goudy old style', 10)).place(x=25,y=((51*pos)+30))
                    #ttk.Label(win4, text='|',font= ('Goudy old style', 10)).place(x=60,y=((51*pos)+30))
                    if square[pos][-6]=='CARRYFORWARD':
                        ttk.Label(win4, text='NRML',font= ('Goudy old style', 10)).place(x=65,y=((51*pos)+30))
                    if square[pos][-6]=='INTRADAY':
                        ttk.Label(win4, text='MIS',font= ('Goudy old style', 10)).place(x=65,y=((51*pos)+30))
                    for s in sl_tp:
                        if sl_tp[s][0]==square[pos][0]:
                            ttk.Label(win4, text=f'SL- {sl_tp[s][2]}',font= ('Goudy old style', 10)).place(x=110,y=((51*pos)+30))
                            ttk.Label(win4, text=f'TG- {sl_tp[s][3]}',font= ('Goudy old style', 10)).place(x=175,y=((51*pos)+30))
                        break
                    ttk.Button(win4,text="MODIFY",width=7.5,command=partial(modify,i["tradingsymbol"])).place(x=240,y=((51*pos)+25))
                    pos+=1
        my_canvas.configure(scrollregion = my_canvas.bbox("all"))

    def sltp():
        while True:    
            if datetime.strptime('09:15','%H:%M').time()<=datetime.now().time():
                break
            time.sleep(1)
        while datetime.strptime('09:15','%H:%M').time()<=datetime.now().time()<=datetime.strptime('15:30','%H:%M').time():
            positons=square.copy()
            st=sl_tp.copy()
            for p in positons:
                for s in st:
                    if positons[p][0]==st[s][0]:
                        if st[s][2]!=None or st[s][3]!=None:
                            ltp=obj.ltpData("NFO",st[s][0],positons[p][1])['data']['ltp']
                            if st[s][1]=='BUY':
                                if (st[s][2]!=None and st[s][2]>=ltp) or (st[s][3]!=None and st[s][3]<=ltp):
                                    qty=positons[p][2]
                                    for i in range(0,int(qty/st[s][4])):
                                        place_order(positons[p][0],positons[p][1],"SELL",positons[p][4],st[s][4],"MARKET",'0')
                                        qty=qty-st[s][4]
                                    if qty>0:
                                        place_order(positons[p][0],positons[p][1],"SELL",positons[p][4],qty,"MARKET",'0')
                                    print(f"SL or Target hit at {ltp} in {positons[p][0]}")
                                    sl_tp.pop(s)
                                    for item in win4.winfo_children():
                                        item.destroy()
                                    Position()
                            elif st[s][1]=='SELL':
                                if (st[s][2]!=None and st[s][2]<=ltp) or (st[s][3]!=None and st[s][3]>=ltp):
                                    qty=positons[p][2]
                                    for i in range(0,int(qty/st[s][4])):
                                        place_order(positons[p][0],positons[p][1],'BUY',positons[p][4],st[s][4],"MARKET",'0')
                                        qty=qty-st[s][4]
                                    if qty>0:
                                        place_order(positons[p][0],positons[p][1],'BUY',positons[p][4],qty,"MARKET",'0')
                                    print(f"SL or Target hit at {ltp} in {positons[p][0]}")
                                    sl_tp.pop(s)
                                    for item in win4.winfo_children():
                                        item.destroy()
                                    Position()
                        break

    def modify(a):
        global idnt,ism
        idnt=a
        symlabl.config(text=a)
        for s in sl_tp:
            if sl_tp[s][0]==a:
                if sl_tp[s][2]!=None:
                    msl.insert(0,f'{sl_tp[s][2]}')
                if sl_tp[s][3]!=None:
                    mtg.insert(0,f'{sl_tp[s][3]}')
                ism=1
                break
        show_frame(win3)

    def getTokenInfo(p,q,r,s,t,u):
        if p.get()==1:
            NB='NIFTY'
        elif q.get()==1:
            NB='BANKNIFTY'
        if r.get()==1:
            pe_ce='CE'
        elif s.get()==1:
            pe_ce='PE'
        return token_df[((token_df['name'] == NB) & (token_df['strike'] == int(t.get())) & (token_df['symbol'].str.endswith(pe_ce)) & (token_df['expiry']==datetime.strptime(u.get(),"%d-%m-%Y")))] 

    def freeze(x,y):
        if x.get()==1:
            return 1800
        elif y.get()==1:
            return 1200

    def misORNnrml(a,b):
        if a.get()==1:
            return "CARRYFORWARD"
        elif b.get()==1:
            return "INTRADAY"     

    def mkt_lmt():
        if var3.get()==1:
            return "MARKET"
        elif var4.get()==1:
            return "LIMIT" 

    def pris():
        if var3.get()==1:
            return '0'
        elif var4.get()==1:
            return PRICE.get() 

    def check(a,b):
        if a.get()==1:
            b.set('0')
        elif a.get()==0:
            b.set('1')

    def bothcheck(a,b):
        if a.get()==1:
            b.set('1')
        elif a.get()==0:
            b.set('0')

    def abc(x,y):
        if x.get()==1:
            y.config(state=NORMAL)
        else:
            y.config(state=DISABLED)

    def checkif():
        if var1.get()==0 and var2.get()==0:
            print("Please select mis or nrml")
            return True
        if var5.get()==0 and var6.get()==0:
            print("Please select Nifty or Banknifty")
            return True
        if SPRICE.get()=="":
            print("Please provide strike price")
            return True
        if int(SPRICE.get()) not in token_df['strike'].values:
            print("Please select correct strike price")
            return True
        if var7.get()==0 and var8.get()==0:
            print("Please select CE or PE")
            return True
        if var4.get()==1 and PRICE.get()=="":
            print("Please provide price")
            return True
        if QTY.get()=="":
            print("Please provide qty")
            return True
        if var5.get()==1:
            if int(QTY.get())%50!=0:
                print("Please provide valid qty in multiple of 50")
                return True
        if var6.get()==1:
            if int(QTY.get())%25!=0:
                print("Please provide valid qty in multiple of 25")
                return True

    def MISf():
        check(var1,var2)
    var1 = tk.IntVar()
    MIS = ttk.Checkbutton(win1,text='MIS',variable = var1,command=MISf).place(x=15,y=15)

    def NRMLf():
        check(var2,var1)
    var2 = tk.IntVar()
    NRML = ttk.Checkbutton(win1,text='NRML',variable = var2,command=NRMLf).place(x=80,y=15)
    var2.set('1')

    def MKTf():
        check(var3,var4)
        abc(var4,PRICE)
    var3 = tk.IntVar()
    MARKET = ttk.Checkbutton(win1,text='MARKET',variable = var3,command=MKTf).place(x=160,y=15)
    var3.set('1')

    def LIMITf():    
        check(var4,var3)
        if var4.get()==0:
            PRICE.delete('0','end')
        abc(var4,PRICE)
    var4 = tk.IntVar()
    LIMIT = ttk.Checkbutton(win1,text='LIMIT',variable = var4,command=LIMITf).place(x=245,y=15)

    def NIFTYf():    
        check(var5,var6)
    var5 = tk.IntVar()
    NIFTY = ttk.Checkbutton(win1,text='NIFTY',variable = var5,command=NIFTYf).place(x=15,y=50)

    def BANKf():    
            check(var6,var5)
    var6 = tk.IntVar()
    BANK = ttk.Checkbutton(win1,text='BANKNIFTY',variable = var6,command=BANKf).place(x=15,y=75)
    var6.set('1')

    #Entryboxs
    ttk.Label(win1,text='STRIKE PRICE',font= ('Goudy old style', 10)).place(x=120,y=50)
    SPRICE = ttk.Entry(win1,width=10)
    SPRICE.place(x=120,y=70)

    ttk.Label(win1,text='PRICE',font= ('Goudy old style', 10)).place(x=120,y=105)
    PRICE = ttk.Entry(win1,width=10,state=DISABLED)
    PRICE.place(x=120,y=125)

    def CEf():
        check(var7,var8)
    var7 = tk.IntVar()
    CEB = ttk.Checkbutton(win1,text='CE',variable = var7,command=CEf).place(x=215,y=110)

    def PEf():
        check(var8,var7)
    var8 = tk.IntVar()
    PEB = ttk.Checkbutton(win1,text='PE',variable = var8,command=PEf).place(x=260,y=110)

    ttk.Label(win1,text='QTY.',font= ('Goudy old style', 10)).place(x=15,y=105)
    QTY = ttk.Entry(win1,width=10)
    QTY.place(x=15,y=125)

    a=list(token_df.drop_duplicates(subset='expiry')['expiry'].dt.strftime('%d-%m-%Y').values)

    ttk.Label(win1,text='EXIPRY',font= ('Goudy old style', 10)).place(x=220,y=50)
    EXP=ttk.Combobox(win1,value=a,width=10)
    EXP.place(x=220,y=70)
    EXP.current(0)

    def SLf():
        if var10.get()==0:
            STOPLOSS.delete('0','end')
        abc(var10,STOPLOSS)
    var10 = tk.IntVar()
    STOPLOSSB = ttk.Checkbutton(win1,text='STOPLOSS',variable = var10,command=SLf).place(x=15,y=155)
    STOPLOSS = ttk.Entry(win1,width=10)
    STOPLOSS.place(x=15,y=180)
    var10.set('1')

    def TPf():
        if var11.get()==0:
            TARGET.delete('0','end')
        abc(var11,TARGET)
    var11 = tk.IntVar()
    TARGETB = ttk.Checkbutton(win1,text='TARGET',variable = var11,command=TPf).place(x=120,y=155)
    TARGET = ttk.Entry(win1,width=10,state=DISABLED)
    TARGET.place(x=120,y=180)

    symlabl=ttk.Label(win3,text='',font= ('Goudy old style', 15))
    symlabl.pack(pady=30)

    def canb():
        global ism
        show_frame(win2)
        msl.delete('0','end')
        mtg.delete('0','end')
        ism=0
    cancelb=ttk.Button(win3,text="CANCEL",command=canb)
    cancelb.place(x=60,y=180)

    ttk.Label(win3,text='STOPLOSS',font= ('Goudy old style', 10)).place(x=60,y=90)
    msl = ttk.Entry(win3,width=10)
    msl.place(x=60,y=110)

    ttk.Label(win3,text='TARGET',font= ('Goudy old style', 10)).place(x=180,y=90)
    mtg = ttk.Entry(win3,width=10)
    mtg.place(x=180,y=110)

    def modifybf():
        global idnt,ism,sp,c
        st=sl_tp.copy()
        if ism==1:
            for s in st:
                if st[s][0]==idnt:
                    if msl.get()=='' and mtg.get()=='':
                        sl_tp.pop(s)
                    elif msl.get()=='':
                        sl_tp[s][2]=None
                        sl_tp[s][3]=float(mtg.get())
                    elif mtg.get()=='':
                        sl_tp[s][3]=None
                        sl_tp[s][2]=float(msl.get())
                    else:
                        sl_tp[s][3]=float(mtg.get())
                        sl_tp[s][2]=float(msl.get())
                    break
        elif ism==0:
            for s in square:
                if square[s][0]==idnt:
                    if msl.get()=='' and mtg.get()=='':
                        print('Please fill SL or Target')
                        return True
                    elif msl.get()=='':
                        sl_tp[sp]=[idnt,square[s][3],None,float(mtg.get()),square[s][-5]]
                    elif mtg.get()=='':
                        sl_tp[sp]=[idnt,square[s][3],float(msl.get()),None,square[s][-5]]
                    else:
                        sl_tp[sp]=[idnt,square[s][3],float(msl.get()),float(mtg.get()),square[s][-5]]
                    break
        if len(sl_tp)>0 and c==0:
            executor.submit(sltp)
            c=1
        ism=0
        sp+=1
        msl.delete('0','end')
        mtg.delete('0','end')
        for item in win4.winfo_children():
            item.destroy()
        Position()
        show_frame(win2)
    modifyb=ttk.Button(win3,text="MODIFY",command=modifybf)
    modifyb.place(x=180,y=180)

    #button
    def buybf():
        if checkif()==True:
            return True
        global ki,sp
        TokenInfo=getTokenInfo(var5,var6,var7,var8,SPRICE,EXP)
        basket[ki]=[TokenInfo['symbol'].iloc[0],TokenInfo['token'].iloc[0],int(QTY.get()),'BUY',misORNnrml(var2,var1),freeze(var5,var6),mkt_lmt(),pris()]
        pod=obj.position()
        if pod['status']==True and pod['data']!=None:
            p=pd.DataFrame(pod['data'])
            p=p.astype({'netqty': int})
            p=p[p["netqty"]!=0]
            st=sl_tp.copy()
            for s in st:
                if sl_tp[s][0]==TokenInfo['symbol'].iloc[0]:
                    if sl_tp[s][0] not in p["tradingsymbol"].values:
                        sl_tp.pop(s)
            if TokenInfo['symbol'].iloc[0] not in p["tradingsymbol"].values:
                if var10.get()==1 and var11.get()==1:
                    if STOPLOSS.get()=='':
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',round((float(pris())-(float(pris())*0.05)),2),float(TARGET.get()),freeze(var5,var6)]
                    else:
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',float(STOPLOSS.get()),float(TARGET.get()),freeze(var5,var6)]
                elif var10.get()==1 and var11.get()==0:
                    if STOPLOSS.get()=='':
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',round((float(pris())-(float(pris())*0.05)),2),None,freeze(var5,var6)]
                    else:
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',float(STOPLOSS.get()),None,freeze(var5,var6)]
                elif var10.get()==0 and var11.get()==1:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',None,float(TARGET.get()),freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',None,None,freeze(var5,var6)]
        else:
            if var10.get()==1 and var11.get()==1:
                if STOPLOSS.get()=='':
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',round((float(pris())-(float(pris())*0.05)),2),float(TARGET.get()),freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',float(STOPLOSS.get()),float(TARGET.get()),freeze(var5,var6)]
            elif var10.get()==1 and var11.get()==0:
                if STOPLOSS.get()=='':
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',round((float(pris())-(float(pris())*0.05)),2),None,freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',float(STOPLOSS.get()),None,freeze(var5,var6)]
            elif var10.get()==0 and var11.get()==1:
                sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',None,float(TARGET.get()),freeze(var5,var6)]
            else:
                sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'BUY',None,None,freeze(var5,var6)]
        print(f"ORDER {ki+1}: SYMBOL- {basket[ki][0]}, QTY- {basket[ki][2]}, TRANSACTION- {basket[ki][3]}, ORDER TYPE- {basket[ki][-2]}, PRODUCT- {basket[ki][-4]}, PRICE- {basket[ki][-1]}, SL- {sl_tp[sp][2]}, TARGET- {sl_tp[sp][3]}")
        PRICE.delete('0','end')
        PRICE.config(state=DISABLED)
        EXP.current(0)
        QTY.delete('0','end')
        SPRICE.delete('0','end')
        STOPLOSS.delete('0','end')
        STOPLOSS.config(state=NORMAL)
        TARGET.delete('0','end')
        TARGET.config(state=DISABLED)
        var1.set('0')
        var2.set('1')
        var3.set('1')
        var4.set('0')
        var5.set('0')
        var6.set('1')
        var7.set('0')
        var8.set('0')
        var10.set('1')
        var11.set('0')
        ki+=1
        sp+=1
    buyb = ttk.Button(win1,text="ADD FOR BUY",command=buybf)
    buyb.place(x=10,y=210)

    def sellbf():
        if checkif()==True:
            return True
        global ki,sp
        TokenInfo=getTokenInfo(var5,var6,var7,var8,SPRICE,EXP)
        basket[ki]=[TokenInfo['symbol'].iloc[0],TokenInfo['token'].iloc[0],int(QTY.get()),'SELL',misORNnrml(var2,var1),freeze(var5,var6),mkt_lmt(),pris()]
        pod=obj.position()
        if pod['status']==True and pod['data']!=None:
            p=pd.DataFrame(pod['data'])
            p=p.astype({'netqty': int})
            p=p[p["netqty"]!=0]
            st=sl_tp.copy()
            for s in st:
                if sl_tp[s][0]==TokenInfo['symbol'].iloc[0]:
                    if sl_tp[s][0] not in p["tradingsymbol"].values:
                        sl_tp.pop(s)
            if TokenInfo['symbol'].iloc[0] not in p["tradingsymbol"].values:
                if var10.get()==1 and var11.get()==1:
                    if STOPLOSS.get()=='':
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',round((float(pris())+(float(pris())*0.05)),2),float(TARGET.get()),freeze(var5,var6)]
                    else:
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',float(STOPLOSS.get()),float(TARGET.get()),freeze(var5,var6)]
                elif var10.get()==1 and var11.get()==0:
                    if STOPLOSS.get()=='':
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',round((float(pris())+(float(pris())*0.05)),2),None,freeze(var5,var6)]
                    else:
                        sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',float(STOPLOSS.get()),None,freeze(var5,var6)]
                elif var10.get()==0 and var11.get()==1:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',None,float(TARGET.get()),freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',None,None,freeze(var5,var6)]
        else:
            if var10.get()==1 and var11.get()==1:
                if STOPLOSS.get()=='':
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',round((float(pris())+(float(pris())*0.05)),2),float(TARGET.get()),freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',float(STOPLOSS.get()),float(TARGET.get()),freeze(var5,var6)]
            elif var10.get()==1 and var11.get()==0:
                if STOPLOSS.get()=='':
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',round((float(pris())+(float(pris())*0.05)),2),None,freeze(var5,var6)]
                else:
                    sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',float(STOPLOSS.get()),None,freeze(var5,var6)]
            elif var10.get()==0 and var11.get()==1:
                sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',None,float(TARGET.get()),freeze(var5,var6)]
            else:
                sl_tp[sp]=[TokenInfo['symbol'].iloc[0],'SELL',None,None,freeze(var5,var6)]
        print(f"ORDER {ki+1}: SYMBOL- {basket[ki][0]}, QTY- {basket[ki][2]}, TRANSACTION- {basket[ki][3]}, ORDER TYPE- {basket[ki][-2]}, PRODUCT- {basket[ki][-4]}, PRICE- {basket[ki][-1]}, SL- {sl_tp[sp][2]}, TARGET- {sl_tp[sp][3]}")
        PRICE.delete('0','end')
        PRICE.config(state=DISABLED)
        EXP.current(0)
        QTY.delete('0','end') 
        SPRICE.delete('0','end')
        STOPLOSS.delete('0','end')
        STOPLOSS.config(state=NORMAL)
        TARGET.delete('0','end')
        TARGET.config(state=DISABLED)
        var1.set('0')
        var2.set('1')
        var3.set('1')
        var4.set('0')
        var5.set('0')
        var6.set('1')
        var7.set('0')
        var8.set('0')
        var10.set('1')
        var11.set('0')
        ki+=1
        sp+=1
    sellb = ttk.Button(win1,text="ADD FOR SELL",command=sellbf)
    sellb.place(x=105,y=210)

    def placef():
        global c
        global ki
        bskt=basket.copy()
        for symb in bskt:
            basket.pop(symb)
            for i in range(0,int(bskt[symb][2]/bskt[symb][-3])):
                place_order(bskt[symb][0],bskt[symb][1],bskt[symb][3],bskt[symb][-4],bskt[symb][-3],bskt[symb][-2],bskt[symb][-1])
                bskt[symb][2]=bskt[symb][2]-bskt[symb][-3]
            if bskt[symb][2]>0:
                place_order(bskt[symb][0],bskt[symb][1],bskt[symb][3],bskt[symb][-4],bskt[symb][2],bskt[symb][-2],bskt[symb][-1])
            for s in sl_tp:
                if bskt[symb][0]==sl_tp[s][0] and sl_tp[s][2]==0:
                    ltp=obj.ltpData("NFO",sl_tp[s][0],bskt[symb][1])['data']['ltp']
                    if sl_tp[s][1]=='BUY':
                        sl_tp[s][2]=round((ltp-(ltp*0.05)),2)
                        break
                    elif sl_tp[s][1]=='SELL':
                        sl_tp[s][2]=round((ltp+(ltp*0.05)),2)
                        break
        if len(sl_tp)>0 and c==0:
            executor.submit(sltp)
            c=1
        ki=0
        if len(bskt)>0:
            print("Orders Placed")
        else:
            print('No Order')
    placeb = ttk.Button(win1,text="PLACE ORDERS",command=placef)
    placeb.place(x=215,y=175)
        
    def positionsbf():
        show_frame(win2)
        for item in win4.winfo_children():
            item.destroy()
        Position()
    positionsb = ttk.Button(win1,text="POSITIONS",command=positionsbf,width=13)
    positionsb.place(x=215,y=140)

    def withdrawf():
        global ki,sp
        if ki>0:
            basket.popitem()
            sl_tp.popitem()
            print(f"ORDER {ki} WITHDRAWN")
            ki-=1
            sp-=1
        else:
            print('NO ORDER TO WITHDRAW')
    withdrawb = ttk.Button(win1,text="WITHDRAW ORDER",command=withdrawf)
    withdrawb.place(x=200,y=210)

    def squareoff():
        st=sl_tp.copy()
        for slct in square:
            if square[slct][-2].get()==1:
                if square[slct][3]=='BUY':
                    qty=square[slct][2]
                    for i in range(0,int(square[slct][2]/square[slct][5])):
                        place_order(square[slct][0],square[slct][1],"SELL",square[slct][-6],square[slct][-5],square[slct][-4],square[slct][-3])
                        qty=qty-square[slct][5]
                    if qty>0:
                        place_order(square[slct][0],square[slct][1],"SELL",square[slct][-6],qty,square[slct][-4],square[slct][-3])
                elif square[slct][3]=='SELL':
                    qty=square[slct][2]
                    for i in range(0,int(square[slct][2]/square[slct][5])):
                        place_order(square[slct][0],square[slct][1],"BUY",square[slct][-6],square[slct][-5],square[slct][-4],square[slct][-3])
                        qty=qty-square[slct][5]
                    if qty>0:
                        place_order(square[slct][0],square[slct][1],"BUY",square[slct][-6],qty,square[slct][-4],square[slct][-3])
                for s in st:
                    if st[s][0]==square[slct][0]:
                        sl_tp.pop(s)
                        break
        for item in win4.winfo_children():
            item.destroy()
        Position()
    squareoffb=ttk.Button(win2,text="SQUAREOFF",command=squareoff)
    squareoffb.place(x=60,y=212)

    def selectf():
        if var9.get()==1:
            if len(square)>0:
                for select in square:
                    square[select][-2].set('1')
        elif var9.get()==0:
            if len(square)>0:
                for select in square:
                    square[select][-2].set('0')
    var9=tk.IntVar()
    selectb=ttk.Checkbutton(win2,text="ALL",variable = var9,command=selectf)
    selectb.place(x=10,y=212)

    def back1f():
        show_frame(win1)
    back1 = ttk.Button(win2,text="BACK",command=back1f)
    back1.place(x=235,y=212)

    def convertf():
        for slct in square:
            if square[slct][-2].get()==1:
                if square[slct][4]=="CARRYFORWARD":
                    convert(square[slct][4],"INTRADAY",square[slct][0],square[slct][3],square[slct][2])
                elif square[slct][4]=="INTRADAY":
                    convert(square[slct][4],"CARRYFORWARD",square[slct][0],square[slct][3],square[slct][2])
        for item in win4.winfo_children():
            item.destroy()
        Position()
    convertb=ttk.Button(win2,text="CONVERT",command=convertf)
    convertb.place(x=147,y=212)

    my_canvas = tk.Canvas(win0,width=295,height=202,yscrollincrement=51)
    my_canvas.pack(side=LEFT, fill=BOTH, expand=True)
    my_scrollbar = ttk.Scrollbar(win0,orient=VERTICAL,command=my_canvas.yview)
    my_scrollbar.pack(side=RIGHT, fill=Y)

    my_canvas.configure(yscrollcommand=my_scrollbar.set)
    my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion = my_canvas.bbox("all")))

    # win3
    win4 = tk.Frame(my_canvas)
    my_canvas.create_window((0,0), window=win4, anchor="nw",width=295)
    show_frame(win1)
    win.mainloop()
    try:
        logout=obj.terminateSession(USER_NAME)
        print("Logout Successfull")
    except Exception as e:
        print("Logout failed: {}".format(e))
