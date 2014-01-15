# -*- coding: utf-8 -*-
'''

Use an Amazon Web Services DynamoDB table as a Pillar data source

Installation:
-------------

    - Create a directory on the salt master for custom extension modules (if you don't already have one)
      e.g. /srv/salt/ext

    - In your master config (e.g. /etc/salt/master):

.. code-block:: yaml

    extension_modules : /srv/salt/ext

    - Create a subdirectory of the extension modules directory named 'pillar'

    - Copy this dynamo_pillar.py to the pillar subdirectory

    - Make sure that you have the python boto library installed (`pip install boto`)

    - Create a boto configuration file to hold your AWS credentials
      (see: http://code.google.com/p/boto/wiki/BotoConfig)



Configuration:
--------------

In the master config file:

.. code-block:: yaml

    ext_pillar:
        - dynamo:
            table: my_pillar_table  # REQUIRED - set to your DynamoDB table name
            region: us-east-1       # Optional - default is 'us-east-1'
            id_field: id            # Optional - the field to query for minion's id; default is 'id'



Usage:
------

 - Create a DynamoDB table with a primary hash key field named `id`

 - Create a record for each minion, with the minion's id in the primary hash key field

 - Create additional key-value pairs for each value you want to store in the pillar

 - Keys which include the '.' character, will be transformed into a hierarchical python dict
        e.g. if your DynamoDB record looks like this:
.. code-block:: yaml

            id : minion1
            ssh.port : 22
            ssh.password.authentication : yes
            ssh.password.permitEmpty : no
            foo.bar.baz : fiz

        the returned pillar for the node will be:
.. code-block:: python

            {'ssh' : {
                'port' : '22',
                'password' : {
                    'authentication' : 'yes',
                    'permitEmpty' : no,
                },
             'foo' : {
                 'bar' : {
                     'baz' : 'fiz'
                 }}}


'''

__author__ = 'Jason Denning <jason@ngeniux.com>'
__copyright__ = 'Copyright (c) 2014 Jason Denning'
__license__ = 'Apache License v2.0 - http://www.apache.org/licenses/LICENSE-2.0'
__version__ = '0.2'



from salt.exceptions import SaltInvocationError

import logging

log = logging.getLogger(__name__)


__virtualname__ = 'dynamo'

# Import Boto libraries
HAS_BOTO = False
try:
    import boto.dynamodb2
    from boto.dynamodb2.table import Table
    HAS_BOTO = True

except ImportError:
    pass

# Import JSON
HAS_JSON = False
try:
    import json
    HAS_JSON = True
except ImportError:
    pass


def __virtual__():
    if not HAS_BOTO:
        log.error("DynamoDB ext_pillar is configured, but unable to load boto.dynamodb2 library!")
        return(False)

    if not HAS_JSON:
        log.error("DynamoDB ext_pillar is configured, but unable to load json library!")
        return(False)

    log.debug("Loading DynamoDB ext_pillar")
    return(__virtualname__)

def key_value_to_tree(data):
    """
    Builds a hierarchical dict from a flat-namespaced dict.
    e.g. given : {'foo.bar.baz' : 1, 'foo.biz' : 'a'}
    will return : {'foo' : {'bar' : {'baz' : 1}, 'biz' : 'a'} }
    """
    tree = {}
    for flatkey, value in data.items():
        t = tree
        keys = flatkey.split('.')
        for key in keys:
            if key == keys[-1]:
                # last key, so set the value
                t[key] = value
            else:
                t = t.setdefault(key, {})
    return(tree)

def ext_pillar(minion_id, pillar, **kw):
    '''
    Get the Pillar data from DynamoDB for the given ``minion_id``.
    '''

    table_name = kw.get('table', None)
    if not table_name:
        # table is not set in config
        raise SaltInvocationError('ext_pillar.dynamo: table name is not defined in ext_pillar config!')
    id_field = kw.get('id_field', 'id')

    try:
        minion_table = Table(table_name)
        log.debug("ext_pillar.dynamo: Connected to table `%s`"% table_name)

    except Exception, e:
        error_msg = "ext_pillar.dynamo: Unable to connect to DyanmoDB - %s"% e.msg
        raise SaltInvocationError(error_msg)

    try:
        # Setup a kwarg dict so that we can have variable 'id' fieldnames
        minion_query_args = {}
        minion_query_args[id_field] = minion_id
        # Query for the minion_id
        minion_record = minion_table.get_item(**minion_query_args)
        # Copy Dynamo Item to dict
        pillar_data = {}
        for k, v in minion_record.items():
            pillar_data[k] = v

        # Delete the id key from the data_dict
        del pillar_data[id_field]

        # Convert flat-namespaced dict to hierarchical dict
        pillar_data = key_value_to_tree(pillar_data)
        return(pillar_data)

    except Exception, e:
        error_msg = "ext_pillar.dynamo: Unable to load pillar data for `%s` - %s"% (minion_id, e.msg)
        raise SaltInvocationError(error_msg)

