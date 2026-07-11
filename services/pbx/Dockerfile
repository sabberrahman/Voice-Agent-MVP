FROM bytedesk/freeswitch:latest

ENV PKG_CONFIG_PATH=/usr/local/freeswitch/lib/pkgconfig:/usr/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      git \
      libspeexdsp-dev \
      libssl-dev \
      pkg-config \
      zlib1g-dev \
    && git clone --recurse-submodules https://github.com/sptmru/freeswitch_mod_audio_stream.git /tmp/mod_audio_stream \
    && cmake -S /tmp/mod_audio_stream -B /tmp/mod_audio_stream/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /tmp/mod_audio_stream/build --target install -j"$(nproc)" \
    && rm -rf /tmp/mod_audio_stream /var/lib/apt/lists/*

COPY conf/directory/default/1001.xml /voxagent-freeswitch/directory/default/1001.xml
COPY conf/directory/default/1002.xml /voxagent-freeswitch/directory/default/1002.xml
COPY conf/dialplan/default/10_extensions.xml /voxagent-freeswitch/dialplan/default/10_extensions.xml
COPY conf/dialplan/default/20_placeholders.xml /voxagent-freeswitch/dialplan/default/20_placeholders.xml
COPY entrypoint.sh /voxagent-entrypoint.sh

RUN mkdir -p /recordings /var/log/freeswitch \
    && chmod +x /voxagent-entrypoint.sh \
    && chmod -R a+rwX /recordings /var/log/freeswitch /voxagent-freeswitch

ENTRYPOINT ["/voxagent-entrypoint.sh"]
