from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.lib.cli import parse_db_config
import psycopg2
import sys


class DrupalCommand(CkanCommand):
  """
  CKAN Drupal Extension
  
  Usage::
  
     paster drupal load-packages [-c <path to config file>]
  """
  summary = __doc__.split('\n')[0]
  usage = __doc__
  
  def command(self):
    '''
    Parse command line arguments and call appropriate method.
    '''
    if not self.args or self.args[0] in ['--help', '-h', 'help']:
        print self.__doc__
        return

    cmd = self.args[0]
    self._load_config()
    
    if cmd == 'load-packages':
      try:
        self.load_packages()
      except KeyboardInterrupt:
        pass
      
    else:
      print self.__doc__
      
  def load_packages(self):

    #Get our CKAN and Drupal connection string
    
    dbc = parse_db_config('sqlalchemy.url')
    ckan_conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (dbc['db_host'], dbc['db_name'], dbc['db_user'], dbc['db_pass'])
    
    dbd = parse_db_config('ckan.drupal.url')
    drupal_conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (dbd['db_host'], dbd['db_name'], dbd['db_user'], dbd['db_pass'])
    
    # get a connection, if a connect cannot be made an exception will be raised here
    ckan_conn = psycopg2.connect(ckan_conn_string)
    drupal_conn = psycopg2.connect(drupal_conn_string)
   
    # ckan_conn.ckan_cursor will return a ckan_cursor object, you can use this ckan_cursor to perform queries
    ckan_cursor = ckan_conn.cursor()
    drupal_cursor = drupal_conn.cursor()
   
    # execute our Query
    ckan_cursor.execute("""select p.id, 
       p.name, 
       p.title, 
       case when pe1.value is null then '' else pe1.value end, 
       case when p.notes   is null then '' else p.notes   end, 
       case when pe2.value is null then '' else pe2.value end 
      from package p 
      left join package_extra pe1 on p.id = pe1.package_id and pe1.key = 'title_fra'
      left join package_extra pe2 on p.id = pe2.package_id and pe2.key = 'notes_fra'""")
          
    # retrieve the records from the CKAN database and insert into the Drupal database
    for rec in ckan_cursor:
      drupal_cursor.execute("""insert into opendata_package (
  pkg_id,
  pkg_name,
  pkg_title_en,
  pkg_title_fr,
  pkg_description_en,
  pkg_description_fr
) values (%s, %s, %s, %s, %s, %s)""", (rec[0], rec[1], rec[2], rec[3], rec[4], rec[5]))
    
    # Close the connections
    
    drupal_conn.commit()
    drupal_cursor.close()
    drupal_conn.close()
    
    ckan_cursor.close()
    ckan_conn.close()
 
