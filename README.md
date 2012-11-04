# SGE/Galaxy with KT ucloud biz

본 어플리케이션은 KT ucloud biz를 이용한 오토메이션 클라우드 생성 프로그램으로 AWS SQS를 이용합니다.

* 본 어플리케이션은 ucloud API를 사용합니다.

## Requirements

## Usage

$ git clone --recursive git://github.com/hongiiv/ucloud_sge.git

## Examples

```python
#!/usr/bin/python
mport message_server
message_server.delete_db()
message_server.create_db()
message_server.select_db()
message_server.run_request("2","BIOINFORMATICS_01","yes","hongiiv@gamil.com")
```

## Message and Table
table_instance

displayname, userid, serviceofferingid, templateid, diskofferingid, zoneid, usageplantype, date_queued, date_runqueue, date_process_start, date_process_end, date_exception, status_code, clustername, clusteruuid, vm_tot_count, volume_list, private_address, public_address, password, virtual_machine_id

table_volume

displayname_volume, displayname_instance, date_queued, date_runqueue, date_process_start, date_process_end, date_exception, status_code, diskofferingid, virtual_machine_id, clustername, clusteruuid, zoneid, volume_id

table_product

productid, productcode, userid, clustername, status, totnodecount, nodecount, nodeinfo, volumeinfo, datecreate, datefinish, dateterminate,totvolumecount, volumecount

{"serviceofferingid":"94341d94-ccd4-4dc4-9ccb-05c0c632d0b4","templateid": "40b12581-d99e-4c77-bbe2-30fcc49a7300","diskofferingid":"cc85e4dd-bfd9-4cec-aa22-cf226c1da92f","zoneid":"eceb5d65-6571-4696-875f-5a17949f3317","usageplantype":"hourly","user_name":"hongiiv","queued_date":"2012-10-28-17-18","displayname":"3c12da7d-7c4b-46d8-92a6-4d8407d67f1e", "clustername":"BIOINFORMATICS","clusteruuid":"7507d445-92fc-450a-9750-30bb2e133c39", "vm_tot_count":"1 of 2"}

{"displayname_volume":"5536c4ae-bdd8-4dfb-9827-50e898329a3e","displayname_instance":"dd83a730-d74d-4574-be37-b94242744827", "now_date":"2012-10-26-11-50", "clustername":"BIOINFORMATICS", "clusteruuid":"0c9e2615-ea3a-4dac-8ba0-7c272f480a84", "zoneid":"eceb5d65-6571-4696-875f-5a17949f3317"}

TODO:
-----
There is a lot to do to clean up the code and make it worthy of production. This
was just a rough first pass.
