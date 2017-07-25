#!/usr/bin/env python
#coding:utf-8
"""
  Author:   --<>
  Purpose: 
  Created: 2016/3/29
"""

from tkinter import *
from global_list import *
from mbom_dataset import *
import random, string
#import tkintertable as tktable

def createRandomStrings(l,n):
    """create list of l random strings, each of length n"""
    names = []
    for i in range(l):
        val = ''.join(random.choice(string.ascii_lowercase) for x in range(n))
        names.append(val)
    return names

def createData(rows=20, cols=5):
    """Creare random dict for test data"""

    data = {}
    names = createRandomStrings(rows,16)
    colnames = createRandomStrings(cols,5)
    for n in names:
        data[n]={}
        data[n]['label'] = n
    for c in range(0,cols):
        colname=colnames[c]
        vals = [round(random.normalvariate(100,50),2) for i in range(0,len(names))]
        vals = sorted(vals)
        i=0
        for n in names:
            data[n][colname] = vals[i]
            i+=1
    return data

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        
        mbom_db.connect()
        
        re = door_packing_mode.select().where((door_packing_mode.door_type=='S200')&(door_packing_mode.is_wooden==False))\
            .order_by(door_packing_mode.box_id.asc())

       
        self.packing_mode = {}
        for r in re:
            s_s = {}
            if r.packing_desc is not None:
                s_s[1]=r.packing_desc.split(';')
                
            if r.packing_except is not None:
                s_s[2] = r.packing_except.split(';')
                
            self.packing_mode[r.box_id]=s_s
            
        print(self.packing_mode)
        for key in self.packing_mode:
            print(key)
            print(self.packing_mode[key])
            
        #mbom_db.create_tables([door_packing_mode,])
        #mbom_db.create_tables([plist_header,plist_items,mboxes_table,box_mat_logic,boxid_rp_rel])
        #mbom_db.create_tables([s_employee, operate_point, op_permission,login_log,nstd_app_head,nstd_app_link,nstd_mat_fin,nstd_mat_table])
        #nstd_mat_fin.get(nstd_mat_fin.mat_no=='330172045')
        #nstd_mat_fin.delete_instance(nstd_mat_table)
        mbom_db.close()
        '''
        data = createData(40)
        print(data)
        self.pack()
        self.createWidgets()
        '''
        
    def createWidgets(self):
        pass

if __name__ == '__main__':
    root=Tk()
    Application(root) 
    root.mainloop() 
    root.destroy()