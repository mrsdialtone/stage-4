import os
import jinja2
import webapp2

import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), "templates")

#jinja templating setup with HTML autoescaping turned on.
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEFAULT_WALL = 'Public'

error = False
# we set this to False intially because loading the page is not an error condition (only bad comments are).

# We set a parent key on the 'Post' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def wall_key(wall_name=DEFAULT_WALL):
    return ndb.Key('Wall', wall_name)

# These are the objects that will represent our Author and our Post. 
# We're using Object Oriented Programming to create objects in order 
# to put them in Google's Database. These objects inherit Googles 
# ndb.Model class.
class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    name = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class PostWall(webapp2.RequestHandler):
    def post(self):
        global error
        # any function that uses the error variable should have this line. that's because we'll not only be accessing the error variable, but also potentially CHANGING it

        wall_name = self.request.get('wall_name', DEFAULT_WALL)
        post = Post(parent=wall_key(wall_name))

        post.content = self.request.get('content')

        if users.get_current_user():
            post.author = Author(
                identity=users.get_current_user().user_id(),
                name=users.get_current_user().nickname(),
                email=users.get_current_user().email())

        else:
            post.author = Author(
                name='anonymous@anonymous.com',
                email='anonymous@anonymous.com')

         
        if post.content and (not post.content.isspace()):
            error = False
            # The comment was good! Let's make sure we don't print an error
            post.put()   
                        
        else:            
            error = True
            # uh oh the comment was bad. We'll have to print an error message
            self.redirect ("/base.html")
                             
     
        query_params = {'wall_name': wall_name}
        self.redirect('/?wall_name' + wall_name)

        post_query = Post.query(ancestor=wall_key(wall_name)).order(-Post.date)
        post = post_query.fetch

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(webapp2.RequestHandler):

    def get(self):
        wall_name = self.request.get('wall_name', DEFAULT_WALL)
        post_query = Post.query(
            ancestor=wall_key(wall_name)).order(-Post.date)
        post = post_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'post': post,
            'wall_name': urllib.quote_plus(wall_name),
            'url': url,
            'url_linktext': url_linktext,
            'error': error
            # this ensures we pass the right value of error to the HTML
            }

        template = jinja_env.get_template('stage1notes.html')
        self.response.write(template.render(template_values))

class Lesson2(Handler):
    def get(self):
        self.render ("stage2notes.html")

class Lesson3(Handler):
    def get(self):
        self.render ("stage3notes.html")

class Lesson4(Handler):
    def get(self):
        self.render ("stage4notes.html")

class Lesson5(Handler):
    def get(self):
        self.render ("stage5notes.html")

app = webapp2.WSGIApplication([("/", MainPage), 
                                ('/stage1notes', MainPage),
                                ('/stage2notes', Lesson2),
                                ('/stage3notes', Lesson3),
                                ('/stage4notes', Lesson4),
                                ('/stage5notes', Lesson5),
                                ('/sign', PostWall),
                                ], debug=True)
