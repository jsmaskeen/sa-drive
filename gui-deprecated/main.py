from logutil import logger
from flask import Flask, request, render_template,jsonify,redirect,session
from helpers.drive_util import SADrive
from helpers.general import Generator,get_free_sa
from helpers.utils import humanbytes
import config
import json
import random
import helpers.dbfuncs as dbf
import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,BooleanField
from wtforms.validators import DataRequired
from threading import Thread
from functools import wraps
def update_sas_on_db():
    sas_on_local = {int(i.split('.')[0]) for i in os.listdir(f'{os.getcwd()}\\accounts')}
    sas_on_db = {i['_id'] for i in dbf.get_size_map()}
    sas_not_on_db = sas_on_local - sas_on_db
    if len(sas_not_on_db) !=0:
        print(f'Following SA\'s were not on db: {sas_not_on_db}. Adding them.....')
        for i in sas_not_on_db:
            dbf.insert_size_map(i,0)


app = Flask(__name__)
app.config["SECRET_KEY"] = 'aerfvg5h4ebwabrg42h5t6y4t32'
app.jinja_env.globals.update(humanbytes=humanbytes)

update_sas_on_db()

def get_parents_name(file_id):
    parents = []
    parent= file_id
    while parent != config.parent_id:
        details = dbf.get_file_details(parent)
        parents.append([details['file_name'],details['_id']])
        parent = details['parent_id']
    return parents


class LoginForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Submit")


def is_logged_in(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not 'logged_in' in session:
            return redirect('/')
        return fn(*args, **kwargs)
    return decorated_view

@app.route('/',methods=['GET','POST'])
def index():
    if 'logged_in' in session:
        return redirect('/drive')

    username = None
    password = None
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        form.username.data = ''
        password = form.password.data
        form.password.data = ''
        if username == config.username_for_logging_into_sa_drive and password == config.password_for_logging_into_sa_drive:
            session['logged_in'] = True
            return redirect('/drive')
        else:
            return "Err 401"

    return render_template('login.html',username=username, passowrd=password,form=form,space_details = dbf.space_details())



@app.route('/drive')
@is_logged_in
def drive():
    children = dbf.find_children(config.parent_id)
    starred_children = dbf.get_starred_children(config.parent_id)
    form = SearchForm()
    return render_template('drive.html',items=children,starred_items = starred_children,this_id = config.parent_id,form=form)





@app.route('/get_progress',methods=['POST'])
@is_logged_in
def progress():
    unique_num = request.json['ulnum']
    try:
        with open(f'ProgressFiles\\{unique_num}.json','r') as f:
            data = f.read()
    except:
        data = {}
    return data

def upload_file(file,parent_folder_id):
    stream_bytes = file.stream
    stream_bytes.seek(0,2)
    size = stream_bytes.tell()
    del stream_bytes
    sa_numbers = get_free_sa(dbf.get_size_map(),size)
    # sa_number = random.choice(sa_numbers)
    sa_number = sa_numbers[0]
    drive = SADrive(sa_number)
    worker = Generator(drive.upload_file(file.filename, parent_folder_id,file.stream))
    for prog in worker:
        # with open(f'ProgressFiles\\{unique_ul_num}.json','w') as f:
        #     f.write(json.dumps({file.filename:prog}))
        print(f'{file.filename} - {prog}')
    uled_file_details = worker.value
    dbf.insert_file(uled_file_details['id'],uled_file_details['title'],uled_file_details['parents'][0]['id'],int(uled_file_details['fileSize']),'file',int(sa_number),False)
    return uled_file_details


class UploadThread(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def get_parent_id_for_each_file_path(file_paths,main_id):
    tmp_drive = SADrive(0)
    ls = []
    for i in file_paths:
        parts = i.split('/')
        _id = main_id
        for j in parts[1:-1]:
            folder_id = dbf.folder_exists(j,_id)
            if folder_id:
                _id = folder_id
            else:
                tmp_id = tmp_drive.create_folder(j,_id)
                dbf.insert_file(tmp_id,j,_id,0,'folder',0,False)
                _id = tmp_id
        ls.append(_id)
    return ls

@app.route("/upload", methods=("POST",))
@is_logged_in
def upload():
    files = request.files.getlist("files")
    file_paths = json.loads(request.form.get("file_paths"))
    parent_folder_id = request.form.get('parent_id')
    is_folder = request.form.get('is_folder')
    print(f"{files=}")
    print(f"{file_paths=}")
    unique_ul_num = request.form.get('ulnum')
    if parent_folder_id == 'root':
        parent_folder_id = config.parent_id
    uled_file_details_ls = []
    # # with open(f'ProgressFiles\\{unique_ul_num}.json','w') as f:
    # #     f.write('{}')
    threads = []
    if is_folder == 'false':
        for file in files:
            t = UploadThread(target=upload_file,args=(file,parent_folder_id,))
            threads.append(t)
        
        for x in threads:
            x.start()

        # Wait for all of them to finish
        for x in threads:
            uled_file_details_ls.append(x.join())
        
        return jsonify(uled_file_details_ls)
    elif is_folder == 'true':
        tmp_drive = SADrive(0)
        fol_name = file_paths[0].split('/')[0]
        further_parent_id = tmp_drive.create_folder(fol_name,parent_folder_id)
        dbf.insert_file(further_parent_id,fol_name,parent_folder_id,0,'folder',0,False)
        parent_id_ls = get_parent_id_for_each_file_path(file_paths,further_parent_id)

        for i in range(len(files)):
            t = UploadThread(target=upload_file,args=(files[i],parent_id_ls[i],))
            threads.append(t)
        for x in threads:
            x.start()

    # Wait for all of them to finish
    for x in threads:
        uled_file_details_ls.append(x.join())
    
    return jsonify(uled_file_details_ls)


def del_file(sa_num,file_id):
    drive = SADrive(int(sa_num))
    drive.delete_file(file_id)
    dbf.delete_file(file_id)


def del_folder(sa_num,file_id):
    children = dbf.find_children(file_id)
    for child in children:
        if child['type'] == 'file':
            del_file(child['service_acc_num'],child['_id'])
        elif child['type'] == 'folder':
            del_folder(child['service_acc_num'],child['_id'])
    del_file(sa_num,file_id)

@app.route("/delete", methods=("POST",))
@is_logged_in
def delete():
    file_id = request.json['file_id']
    details = dbf.get_file_details(file_id)
    if details['type'] == 'file':
        drive = SADrive(int(details['service_acc_num']))
        drive.delete_file(file_id)
        dbf.delete_file(file_id)
    elif details['type'] == 'folder':
        del_folder(int(details['service_acc_num']),file_id)
    return "ok"


@app.route("/create_folder", methods=("POST",))
@is_logged_in
def create_folder():
    data = request.json
    parent_id = data['file_id']
    if parent_id == 'root':
        parent_id = config.parent_id
    foldername = data['foldername']
    sa_num = int(random.choice(os.listdir(f'{os.getcwd()}\\accounts')).split('.')[0])
    drive = SADrive(sa_num)
    f = drive.create_folder(foldername,parent_id)
    dbf.insert_file(f,foldername,parent_id,0,'folder',sa_num,False)
    return jsonify({"id":f})


@app.route('/viewfile/<file_id>')
@is_logged_in
def viewfile(file_id):
    return redirect(f'https://drive.google.com/open?id={file_id}')

@app.route('/viewfolder/<folder_id>')
@is_logged_in
def viewfolder(folder_id):
    parent_ls = get_parents_name(folder_id)
    this = parent_ls[0]
    starred_children = dbf.get_starred_children(folder_id)
    parent_ls.reverse()
    children = dbf.find_children(folder_id)
    strn = ["""<a href="/viewfolder/{}" class="link-light link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover" >{}</a>""".format(i[1],i[0]) for i in parent_ls]
    parent_str = ' / '.join(strn) + ' /'
    form = SearchForm()
    return render_template('viewfolder.html',items=children,parent_str=parent_str,starred_items=starred_children,foldername=this[0],this_id=this[1],form=form)

@app.route('/starred')
@is_logged_in
def starred_view():
    children = dbf.get_starred_files()
    form = SearchForm()
    return render_template('starred_files.html',form=form,items=children,starred_items=children)



    

@app.route("/addstar", methods=("POST",))
@is_logged_in
def add_star():
    file_id = request.json['file_id']
    dbf.add_star(file_id)
    return "ok"

@app.route("/removestar", methods=("POST",))
@is_logged_in
def remove_star():
    file_id = request.json['file_id']
    dbf.remove_star(file_id)
    return "ok"



@app.route("/renamefile", methods=("POST",))
@is_logged_in
def rename_file():
    data = request.json
    file_id = data['file_id']
    new_filename = data['filename']
    details = dbf.get_file_details(file_id)
    sa_num = details['service_acc_num']
    drive = SADrive(sa_num)
    drive.rename(file_id,new_filename)
    dbf.rename_file(file_id,new_filename)
    return 'ok'



def share_file_base(sa_num,file_id):
    drive = SADrive(int(sa_num))
    link = drive.share(file_id)
    dbf.share_file(file_id,True)
    return link


def share_folder_recursive(sa_num,file_id):
    children = dbf.find_children(file_id)
    for child in children:
        if child['type'] == 'file':
            dbf.share_file(child['_id'],True)
        elif child['type'] == 'folder':
            share_folder_recursive(child['service_acc_num'],child['_id'])
    dbf.share_file(file_id,True)
    
    


@app.route("/share", methods=("POST",))
@is_logged_in
def share_file():
    file_id = request.json['file_id']
    details = dbf.get_file_details(file_id)
    sa_num = details['service_acc_num']
    if details['type'] == 'folder':
        share_folder_recursive(sa_num,file_id)

    link  = share_file_base(sa_num,file_id)
    return jsonify({'link':link})


def unshare_file_base(sa_num,file_id):
    drive = SADrive(sa_num)
    try:
        drive.unshare(file_id)
    except Exception:
        return 
    dbf.share_file(file_id,False)
    return


def unshare_folder_recursive(sa_num,file_id):
    children = dbf.find_children(file_id)
    for child in children:
        if child['type'] == 'file':
            dbf.share_file(child['_id'],False)
        elif child['type'] == 'folder':
            unshare_folder_recursive(child['service_acc_num'],child['_id'])
    dbf.share_file(file_id,False)


@app.route("/unshare", methods=("POST",))
@is_logged_in
def unshare_file():
    file_id = request.json['file_id']
    details = dbf.get_file_details(file_id)
    sa_num = details['service_acc_num']
    if details['type'] == 'folder':
        unshare_folder_recursive(sa_num,file_id)
    unshare_file_base(sa_num,file_id)
    return "ok"


@app.route('/sasdetails')
@is_logged_in
def sas_details():
    items =[(i['_id'],i['size']) for i in dbf.get_size_map()]
    items.sort(key=lambda x:x[1],reverse=True)
    return render_template('sa_details.html',items=items,space_details = dbf.space_details())

def search_for_file(file_name,fuzzy): 
    if fuzzy:
        actual = []
        hp = SADrive(0)
        ls = hp.search(file_name)
        for i in ls:
            # ce = i['lastModifyingUser']['emailAddress']
            # sa_num = dbf.get_sa_num(ce)
            # if sa_num:
            #     i['']
            tmp  = dbf.get_file_details(i['id'])
            if tmp:
                actual.append(tmp)
    else:
        actual = dbf.search_for_file_contains(file_name)

    return actual

class SearchForm(FlaskForm):
    searched = StringField("What do you want to search ?",validators=[DataRequired()])
    submit = SubmitField("Search")
    fuzzy = BooleanField(label='Fuzzy Search ?')



@app.route('/search',methods=['POST','GET'])
@is_logged_in
def _search():
    if request.method == 'GET':
        return redirect('/')
    form = SearchForm()
    if form.validate_on_submit():
        searched = form.searched.data
        fuzzy = form.fuzzy.data
        if searched not in ['',None]:
            all_files = search_for_file(searched,fuzzy)
            return render_template('search.html',form=form,searched=searched,items=all_files,starred_items=dbf.get_starred_files())
        else:
            return redirect('/')
    else:
        return redirect('/')


if __name__ == "__main__":
    app.run(debug=True,port=5100)