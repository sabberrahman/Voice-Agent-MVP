FROM safarov/freeswitch:latest

COPY conf/directory/default/1001.xml /voxagent-freeswitch/directory/default/1001.xml
COPY conf/directory/default/1002.xml /voxagent-freeswitch/directory/default/1002.xml
COPY conf/dialplan/default/10_extensions.xml /voxagent-freeswitch/dialplan/default/10_extensions.xml
COPY conf/dialplan/default/20_placeholders.xml /voxagent-freeswitch/dialplan/default/20_placeholders.xml
COPY entrypoint.sh /voxagent-entrypoint.sh

RUN mkdir -p /recordings /var/log/freeswitch \
    && chmod +x /voxagent-entrypoint.sh \
    && chmod -R a+rwX /recordings /var/log/freeswitch /voxagent-freeswitch

ENTRYPOINT ["/voxagent-entrypoint.sh"]
