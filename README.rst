salt-pillar-dynamo
==================

This is a external pillar for SaltStack that uses AWS DynamoDB as a data source.

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



