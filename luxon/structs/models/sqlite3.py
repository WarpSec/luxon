# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
from luxon import db
from luxon.structs.models import fields

class Sqlite3(object):
    def __init__(self, model):
        self._table = model.__class__.__name__
        self._fields = model._declared_fields
        self._primary_key = model.primary_key
        self._db_engine = model.db_engine
        self._db_charset = model.db_charset

    # Backup, Drop, Create, Restore.
    def bdcr(self):
        backup = None
        table = self._table
        model_fields = self._fields

        with db() as conn:
            if conn.has_table(self._table):
                # NOTE(cfrademan): Backup table..
                backup = conn.execute("SELECT * FROM %s" % table)
                backup = backup.fetchall()

                # NOTE(cfrademan): Drop exisiting table..
                conn.execute("DROP TABLE %s" % table)

            # NOTE(cfrademan): We need to create the table..
            create = 'CREATE TABLE `%s` (' % table
            sql_fields = []
            for field in model_fields:
                sql_field = None

                column = model_fields[field].name
                null = model_fields[field].null

                if isinstance(model_fields[field], fields.Float):
                    sql_field = " %s REAL" % column

                if isinstance(model_fields[field], fields.Decimal):
                    sql_field = " %s REAL" % column

                if isinstance(model_fields[field], fields.String):
                    sql_field = " %s TEXT" % column

                if isinstance(model_fields[field], fields.Integer):
                    sql_field = " %s INTEGER" % column

                if isinstance(model_fields[field], fields.DateTime):
                    sql_field = " %s TEXT" % column

                if isinstance(model_fields[field], fields.Blob):
                    sql_field = " %s BLOB" % column

                if isinstance(model_fields[field], fields.Text):
                    sql_field = " %s TEXT" % column

                if isinstance(model_fields[field], fields.Enum):
                    sql_field = " %s TEXT" % column

                if null is False:
                    sql_field += ' NOT NULL'

                if self._primary_key.name == column:
                    sql_field += ' PRIMARY KEY'

                if isinstance(model_fields[field], fields.ForeignKey):
                    foreign_keys = []
                    references = []
                    ref_table = model_fields[field]._reference_fields[0]._table

                    for fk in model_fields[field]._foreign_keys:
                        foreign_keys.append('`' + fk.name + '`')
                    foreign_keys = ",".join(foreign_keys)

                    for ref in model_fields[field]._reference_fields:
                        references.append('`' + ref.name + '`')
                    references = ",".join(references)

                    index = ' FOREIGN KEY (%s)' % foreign_keys
                    index += ' REFERENCES %s' % ref_table
                    index += '(%s)' % references
                    index += ' ON DELETE %s' % model_fields[field]._on_delete
                    index += ' ON UPDATE %s' % model_fields[field]._on_update
                    sql_field = index

                if sql_field is not None:
                    sql_fields.append(sql_field)

            create += ",".join(sql_fields)
            create += ')'
            conn.execute(create)

            for field in model_fields:
                if isinstance(model_fields[field], fields.UniqueIndex):
                    index = 'CREATE UNIQUE INDEX'
                    index += ' %s on %s (' % (field, table,)
                    index_fields = []
                    for index_field in model_fields[field]._index:
                        index_fields.append('%s' % index_field.name)
                    index += ",".join(index_fields)
                    index += ')'
                    conn.execute(index)


            # NOTE(cfrademan): Restore table..
            if backup is not None:
                for row in backup:
                    query = "INSERT INTO %s (" % table
                    query += ','.join(row.keys())
                    query += ')'
                    query += ' VALUES'
                    query += ' ('
                    placeholders = []
                    for ph in range(len(row)):
                        placeholders.append('%s')
                    query += ','.join(placeholders)
                    query += ')'
                    conn.execute(query, list(row.values()))
                conn.commit()

