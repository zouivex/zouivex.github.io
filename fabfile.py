from fabric.api import *
import fabric.contrib.project as project
import os
import sys
import datetime
import SimpleHTTPServer
import SocketServer

# Local path configuration (can be absolute or relative to fabfile)
env.deploy_path = 'output'
env.content_path = 'content'

def clean():
    local('rm -rf {deploy_path}'.format(**env))
    local('mkdir {deploy_path}'.format(**env))

def build():
    local('pelican -s pelicanconf.py')

def rebuild():
    clean()
    build()

def regenerate():
    local('pelican -r -s pelicanconf.py')

def serve():
    os.chdir(env.deploy_path)

    PORT = 8000
    class AddressReuseTCPServer(SocketServer.TCPServer):
        allow_reuse_address = True

    server = AddressReuseTCPServer(('', PORT), SimpleHTTPServer.SimpleHTTPRequestHandler)

    sys.stderr.write('Serving on port {0} ...\n'.format(PORT))
    server.serve_forever()

def reserve():
    build()
    serve()

def preview():
    local('pelican -s publishconf.py')

def publish():
    clean()
    local('pelican -s publishconf.py')
    local('ghp-import -b master output')
    local('git push origin master')

def new_post(title):
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d %H:%M:%S")
    current_date_short = now.strftime("%Y-%m-%d")

    post_content = \
        'Title: {0}\nSlug: {1}\nDate: {2}\nModified: {3}\nCategory: blog\nTags: misc\n' \
        .format(title, title, current_date, current_date)

    post_file_name = '{0}-{1}.markdown'.format(current_date_short, title)
    post_file_name = os.path.join(env.content_path, post_file_name)

    f = open(post_file_name,"w")
    f.write(post_content)
    f.close()

    print 'New post crated to: ' + post_file_name

# need test for new_page command!
def new_page(title):
    now = datetime.datetime.now()
    current_date = now.strftime("%Y-%m-%d %H:%M:%S")

    page_content = \
        'Title: {0}\nSlug: {1}\nDate: {2}\nModified: {3}\nCategory: blog\nTags: misc\n' \
        .format(title, title, current_date, current_date)

    page_file_name = '{0}.markdown'.format(title)
    page_file_name = os.path.join('pages', page_file_name)
    post_file_name = os.path.join(env.content_path, post_file_name)

    f = open(post_file_name,"w")
    f.write(post_content)
    f.close()

    print 'New post crated to: ' + post_file_name
