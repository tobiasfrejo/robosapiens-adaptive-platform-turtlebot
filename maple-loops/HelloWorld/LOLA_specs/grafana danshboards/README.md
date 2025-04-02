# Setup Grafana

- Grafana is configured to start with the Full TB3 Mesa devcontainer. The MQTT data source plugin is installed automatically.
- Open [http://localhost:3000](localhost:3000)
- Setup the MQTT data source with the local MQTT broker (localhost:1883)
- Setup the Redis data source with the local Redis server (redis://127.0.0.1:6379)
- Create a new Dashboard or import an existing one



## Transforming data

If you have multiple MQTT streams that should be added to a single panel, a data transformation might be necessary.

In the example (grafana dash test.json), "kLaserScan", "kLidarMask", "kHandlingAnomaly" are shown together in the "Knowledge" panel, and shows the latest action, wether each of the items have been read or written in the Redis database.

Each of them arrives in their own table with columns (time, Str) --- Str is from the key of the JSON-parsed MQTT message (e.g. `'{ "Str": "read" }'`.
Thus, the transformation is started with an OUTER JOIN on time, followed by the renaming of the three `Str` columns.


In the other unamed panel, only a single value is observed. This is the "stage2" (has been renamed in the code to "atomicstage"), that tracks `start_X` and `end_X` of each stage, where we filter to exclude the end values. Furthermore, a "Value mapping" (from the side bar) is added to give better names on the graph. 


