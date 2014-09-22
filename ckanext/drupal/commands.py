
from ckan.lib.cli import CkanCommand
from ckan.lib.cli import parse_db_config
import logging
import psycopg2
import json
import sys


class DrupalCommand(CkanCommand):
    """
    CKAN Drupal Extension

    Usage::

       paster drupal load-packages [-c <path to config file>]
                     load-docs [-c <path to config file>]
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

        self.logger = logging.getLogger('ckanext')

        if cmd == 'load-packages':
            try:
                self.load_packages()
            except KeyboardInterrupt:
                pass
        elif cmd == 'load-docs':
            try:
                self.load_docs()
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
            drupal_cursor.execute("""select count(*) from opendata_package where pkg_id = %s""", (rec[0],))
            row = drupal_cursor.fetchone()
            if row[0] == 0:
                print "Inserting package %s" % (rec[0],)
                try:
                    drupal_cursor.execute("""insert into opendata_package (
  pkg_id,
  pkg_name,
  pkg_title_en,
  pkg_title_fr,
  pkg_description_en,
  pkg_description_fr
) values (%s, %s, %s, %s, %s, %s)""", (rec[0], self.format_drupal_string(rec[1]), self.format_drupal_string(rec[2]),
                                           self.format_drupal_string(rec[3]), self.format_drupal_string(rec[4]),
                                           self.format_drupal_string(rec[5])))
                except psycopg2.DataError, e:
                    self.logger.warn('Postgresql Database Exception %s', e.message)

        # Close the connections

        drupal_conn.commit()
        drupal_cursor.close()
        drupal_conn.close()

        ckan_cursor.close()
        ckan_conn.close()

    def load_docs(self):
        '''
        Load the Virtual Library datasets into the same Drupal table as the Open Data datasets.
        @return: nothing
        '''

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
       case when pe1.value is null then '' else pe1.value end,
       case when pe2.value is null then '' else pe2.value end
      from package p
      left join package_extra pe1 on p.id = pe1.package_id and pe1.key = 'title_ml'
      left join package_extra pe2 on p.id = pe2.package_id and pe2.key = 'description_ml'
      where p.type = 'doc' and p.state = 'active'""")

        # retrieve the records from the CKAN database and insert into the Drupal database
        for rec in ckan_cursor:
            drupal_cursor.execute("""select count(*) from opendata_package where pkg_id = %s""", (rec[0],))
            row = drupal_cursor.fetchone()
            if row[0] == 0:
                titles = json.loads(rec[2])
                descriptions = json.loads(rec[3])
                title_en = ''
                if 'en' in titles:
                    title_en = titles['en']
                title_fr = ''
                if 'fr' in titles:
                    title_fr = titles['fr']
                desc_en = ''
                if 'en' in descriptions:
                    desc_en = descriptions['en']
                desc_fr = ''
                if 'fr' in descriptions:
                    desc_fr = descriptions['fr']
                print "Inserting package %s: %s %s %s: %s %s" % (rec[0], rec[1], title_en, title_fr, desc_en, desc_fr)
                try:
                    drupal_cursor.execute("""insert into opendata_package (
  pkg_id,
  pkg_name,
  pkg_title_en,
  pkg_title_fr,
  pkg_description_en,
  pkg_description_fr
) values (%s, %s, %s, %s, %s, %s)""", (rec[0], rec[1], title_en, title_fr, desc_en, desc_fr))

                except psycopg2.DataError, e:
                    self.logger.warn('Postgresql Database Exception %s', e.message)

        # Close the connections

        drupal_conn.commit()
        drupal_cursor.close()
        drupal_conn.close()

        ckan_cursor.close()
        ckan_conn.close()


    def format_drupal_string(self, ds):
        dstr = ''
        try:
            if len(ds) > 200:
                dstr = u"{0}...".encode('utf-8', 'replace').format(ds[0:200])
            else:
                dstr =  ds.encode('utf-8', 'replace')
        except UnicodeDecodeError, e:
            warn_args = {'drupal_string': ds, 'x_msg': e.message}
            self.logger.warn('Unicode Decode Exception for %(drupal_string)s: %(x_msg)s', warn_args)
            dstr = ''
        dstr = dstr.replace('\xc3\x2e','')
        return dstr
