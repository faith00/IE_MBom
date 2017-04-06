#!/usr/bin/env python
# coding:utf-8
"""
  Author:   10256603<mikewolf.li@tkeap.com>
  Purpose:
  Created: 2016/4/7
"""
from eds_pane import *
from import_pane import *
from mat_fin_pane import *
from proj_release_pane import *
from packing_pane import *
from wbs_bom_pane import *

global login_info

tree_items = ['非标物料导入', 'IE项目列表', '项目release', 'EDS项目处理', '分箱处理', 'WBS BOM查询']


class LoginForm(Toplevel):

    def __init__(self, parent, title=None):
        Toplevel.__init__(self, parent)

        self.withdraw()
        if parent.winfo_viewable():
            self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        if self.parent is not None:
            center(self)

        self.deiconify()  # become visible now

        self.initial_focus.focus_set()

        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def body(self, master):
        self.label1 = Label(master, text='用户名')
        self.label1.grid(row=0, column=0, sticky=W)
        self.uid_entry = Entry(master)
        self.uid_entry.grid(row=0, column=1, columnspan=2,  sticky=EW)
        self.label2 = Label(master, text='密码')
        self.label2.grid(row=1, column=0, sticky=W)
        self.pwd_entry = Entry(master, show='*')
        self.pwd_entry.grid(row=1, column=1, columnspan=2, sticky=EW)
        self.msg_str = StringVar()
        self.label_message = Label(master, textvariable=self.msg_str).grid(
            row=2, column=0, columnspan=3, sticky=W)
        return self.uid_entry

    def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="登陆", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="取消", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def validate(self):
        login_info['uid'] = self.uid_entry.get()
        login_info['pwd'] = self.pwd_entry.get()

        if len(login_info['uid'].strip()) == 0:
            self.msg_str.set('用户名不能为空')
            self.initial_focus = self.uid_entry
            self.initial_focus.focus_set()
            return 0

        puid = ctypes.c_char_p(login_info['uid'].encode('utf-8'))
        ppwd = ctypes.c_char_p(login_info['pwd'].encode('utf-8'))
        pdomain = ctypes.c_char_p(b'tkeasia.com')
        logintype = ctypes.c_uint32()
        loginprovider = ctypes.c_uint32()
        logintype.value = 3
        loginprovider.value = 0
        token = ctypes.pointer(ctypes.c_int32(0))
        ret = ctypes.windll.Advapi32.LogonUserA(
            puid, pdomain, ppwd, logintype, loginprovider, ctypes.byref(token))
        last_error = ctypes.windll.kernel32.GetLastError()
        if ret == 1:
            login_info['status'] = True
            self.get_permission()
            self.log_login()
            return 1
        elif last_error == 1326:
            self.msg_str.set('帐户密码错误')
            self.initial_focus = self.pwd_entry
            self.initial_focus.focus_set()
            return 0
        else:
            value = format_system_message(last_error)
            self.msg_str.set('登陆失败！')
            messagebox.showerror('错误', str(last_error) + ':' + value)
            return 0

    def destroy(self):
        self.initial_focus = None
        Toplevel.destroy(self)

    def cancel(self, event=None):
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

        if pg_db.get_conn():
            pg_db.close()

        if mbom_db.get_conn():
            mbom_db.close()

        sys.exit()

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.destroy()

    def log_login(self):
        if not mbom_db.get_conn():
            mbom_db.connect()

        login_record = login_log.select().where(
            (login_log.employee == login_info['uid']) & (login_log.log_status == True))
        if len(login_record) > 0:
            log_loger = login_log.update(log_status=False).where(
                (login_log.employee == login_info['uid']) & (login_log.log_status == True))
            log_loger.execute()

        log_loger = login_log.insert(
            employee=login_info['uid'], log_status=True, login_time=datetime.datetime.now())
        log_loger.execute()

    def get_permission(self):
        try:
            perm = op_permission.get(
                op_permission.employee == login_info['uid'])
            login_info['perm'] = perm.perm_code
        except op_permission.DoesNotExist:
            pass


class mainframe(Frame):
    import_tab = None
    operat_tab = None
    proj_release_tab = None
    eds_tab = None
    packing_tab = None
    wbs_bom_tab = None

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
        pg_db.connect()
        if not mbom_db.get_conn():
            mbom_db.connect()

    def createWidgets(self):
        self.ntbook = ttk.Notebook(self)

        self.tree = ttk.Treeview(self, columns=(
            'col0'), displaycolumns=(), selectmode='browse')
        self.tree.column('#0', width=150)
        self.tree.column('col0', anchor='w')
        self.tree.heading('#0', text='')
        self.tree.heading('col0', text='')
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.grid(row=0, column=0, sticky=NS)
        ysb.grid(row=0, column=1, sticky=NS)
        xsb.grid(row=1, column=0, sticky=EW)

        tree_root = self.tree.insert('', 'end', text='操作列表', open=True)
        for item in tree_items:
            self.tree.insert(tree_root, 'end', text=item,
                             values=(-1), open=False)

        self.ntbook.grid(row=0, column=2, rowspan=2, sticky=NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        self.ntbook.rowconfigure(0, weight=1)
        self.ntbook.columnconfigure(0, weight=1)
        self.st_msg = StringVar()
        self.status_bar = Label(self, textvariable=self.st_msg, anchor='w')
        self.status_bar.grid(row=2, column=0, columnspan=4, sticky=EW)

        self.tree.bind('<<TreeviewSelect>>', self.select_func)
        self.ntbook.bind('<<NotebookTabChanged>>', self.tab_changed)

    def tab_changed(self, event):
        if not login_info['status']:
            return

        i_sel = int(self.ntbook.index(CURRENT))
        root = self.tree.get_children()
        if not root:
            return
        ch_items = self.tree.get_children(root)
        for item in ch_items:
            if i_sel == int(self.tree.item(item, 'values')[0]):
                self.tree.selection_set(item)
                return

    def select_func(self, event):
        if not login_info['status']:
            return

        select = self.tree.selection()
        if not select:
            return

        sel = select[0]
        #print(self.tree.item(sel, 'values'))
        i_per = int(self.tree.item(sel, 'values')[0])
        # print(i_per)
        s_perm = login_info['perm']

        i_sel = self.ntbook.index(END)

        if i_per == -1:
            nt_title = self.tree.item(sel, 'text')
            i_index = tree_items.index(nt_title)

            if i_index == 0:
                if not self.import_tab and int(s_perm[i_index]) > 0:
                    self.import_tab = import_pane(self)
                    self.ntbook.add(self.import_tab,
                                    text=nt_title, sticky=NSEW)
                    self.tree.set(sel, 'col0', i_sel)
                    self.ntbook.select(i_sel)
                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
            elif i_index == 1:
                if not self.operat_tab and int(s_perm[i_index]) > 0:
                    self.operat_tab = mat_fin_pane(self)
                    self.ntbook.add(self.operat_tab,
                                    text=nt_title, sticky=NSEW)
                    self.tree.set(sel, 'col0', i_sel)
                    self.ntbook.select(i_sel)
                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
            elif i_index == 2:
                if not self.proj_release_tab and int(s_perm[i_index]) > 0:
                    self.proj_release_tab = proj_release_pane(self)
                    self.ntbook.add(self.proj_release_tab,
                                    text=nt_title, sticky=NSEW)
                    self.tree.set(sel, 'col0', i_sel)
                    self.ntbook.select(i_sel)

                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
            elif i_index == 3:
                if not self.eds_tab and int(s_perm[i_index]) > 0:
                    self.eds_tab = eds_pane(self)
                    self.ntbook.add(self.eds_tab, text=nt_title, sticky=NSEW)
                    self.tree.set(sel, 'col0', i_sel)
                    self.ntbook.select(i_sel)
                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
            elif i_index == 4:
                if not self.packing_tab and int(s_perm[i_index]) > 0:
                    self.packing_tab = packing_pane(self)
                    self.ntbook.add(self.packing_tab,
                                    text=nt_title, sticky=NSEW)
                    self.tree.set(sel, 'col0', i_sel)
                    self.ntbook.select(i_sel)
                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
            elif i_index == 5:
                if not self.wbs_bom_tab and int(s_perm[i_index]) > 0:
                    self.wbs_bom_tab = wbs_bom_pane(self)
                    self.ntbook.add(self.wbs_bom_tab,
                                    text=nt_title, sticky=NSEW)
                    self.tree.set(sel,'col0',i_sel)
                    self.ntbook.select(i_sel)
                    self.st_msg.set('')
                else:
                    self.st_msg.set('没有权限')
                    return
                    
        else:
            if int(s_perm[i_per]) <= 0:
                self.st_msg.set('没有权限')
                return

            self.ntbook.select(i_per)

        '''
        if i_per ==0:
            self.ntbook.add(self.import_tab)
        elif i_per ==1:
            self.ntbook.add(self.operat_tab)
        elif i_per ==2:
            self.ntbook.add(self.proj_release_tab)

        self.ntbook.select(i_per)
'''


class Application():

    def __init__(self, root):
        main_frame = mainframe(root)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.grid(row=0, column=0, sticky=NSEW)
        LoginForm(main_frame, '用户登陆')
        # popup.attributes("-toolwindow",1)
        # popup.wm_attributes("-topmost",1)

        # for t in threads:
        #    t.join()

        root.protocol("WM_DELETE_WINDOW", self.quit_func)

    def quit_func(self):
        if pg_db.get_conn():
            pg_db.close()

        if mbom_db.get_conn() and login_info['status']:
            log_loger = login_log.update(logout_time=datetime.datetime.now(), log_status=False).where(
                (login_log.employee == login_info['uid']) & (login_log.log_status == True))
            log_loger.execute()
            mbom_db.close()

        root.destroy()

if __name__ == '__main__':
    root = Tk()
    #root.resizable(0, 0)
    root.wm_state('zoomed')
    root.title(NAME + PUBLISH_KEY + VERSION)
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(size=10)
    root.option_add("*Font", default_font)
    Application(root)
    root.geometry('800x600')
    root.mainloop()
