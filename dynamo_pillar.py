# -*- coding: utf-8 -*-
'''

Use an Amazon Web Services DynamoDB table as a Pillar data source

Installation:
-------------

Configuration:
--------------

In the master config file:

.. code-block:: yaml

    ext_pillar:
        - dynamo:
            table: my_pillar_table  # REQUIRED - set to your DynamoDB table name
            region: us-east-1       # Optional - default is 'us-east-1'
            id_field: id            # Optional - the field to query for minion_id; default is 'id'
            pillar_field: pillar    # Optional - the field that contains JSON formatted pillar data; default is 'pillar'
'''

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
    # Check to see if this ext_pillar is configured
    ext_pillar_sources = [p for p in __opts__.get('ext_pillar', p)]
    if not any(__virtualname__ in p for p in ext_pillar_sources):
        # This pillar was not configured
        return(False)

    if not HAS_BOTO:
        log.error("DynamoDB ext_pillar is configured, but unable to load boto.dynamodb2 library!")
        return(False)

    if not HAS_JSON:
        log.error("DynamoDB ext_pillar is configured, but unable to load json library!")
        return(False)

    log.debug("Loading DynamoDB Pillar")
    return(__virtualname__)


def ext_pillar(minion_id, pillar, **kw):
    '''
    Get the Pillar data from DynamoDB for the given ``minion_id``.
    '''

    table_name = kw.get('table', None)
    if not table_name:
        # table is not set in config
        raise SaltInvocationError('ext_pillar.dynamo: table name is not defined in ext_pillar config!')
    id_field = kw.get('id_field', 'id')
    pillar_field = kw.get('pillar_field', 'pillar')

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
        pillar_data = json.loads(minion_record.get(pillar_field, "{}"))
        return(pillar_data)

    except Exception, e:
        error_msg = "ext_pillar.dynamo: Unable to load pillar data for `%s` - %s"% (minion_id, e.msg)
        raise SaltInvocationError(error_msg)

