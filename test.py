import oracledb

# Instant Client 경로 지정 (oci.dll이 들어있는 폴더)
oracledb.init_oracle_client(lib_dir=r"C:\Users\kosa\Downloads\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9")

print("Oracle Client version:", oracledb.clientversion())