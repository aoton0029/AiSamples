FROM neo4j:5.13-community

# プラグインを事前にダウンロード
ENV NEO4JLABS_PLUGINS=["apoc","graph-data-science"]

# 初回起動でプラグインをダウンロードさせる
RUN mkdir -p /plugins && \
    neo4j start && \
    sleep 30 && \
    neo4j stop

# または手動でプラグインファイルを配置
# COPY plugins/*.jar /plugins/