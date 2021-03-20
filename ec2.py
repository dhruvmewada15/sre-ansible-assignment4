
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
177
178
179
180
181
182
183
184
185
186
187
188
189
190
191
192
193
194
195
196
197
198
199
200
201
202
203
204
205
206
207
208
209
210
211
212
213
214
215
216
217
218
219
220
221
222
223
224
225
226
227
228
229
230
231
232
233
234
235
236
237
238
239
240
241
242
243
244
245
246
247
248
249
250
251
252
253
254
255
256
257
258
259
260
261
262
263
264
265
266
267
268
269
270
271
272
273
274
275
276
277
278
279
280
281
282
283
284
285
286
287
288
289
290
291
292
293
294
295
296
297
298
299
300
301
302
303
304
305
306
307
308
309
310
311
312
313
314
315
316
317
318
319
320
321
322
323
324
325
326
327
328
329
330
331
332
333
334
335
336
337
338
339
340
341
342
343
344
345
346
347
348
349
350
351
352
353
354
355
356
357
358
359
360
361
362
363
364
365
366
367
368
369
370
371
372
373
374
375
376
377
378
379
380
381
382
383
384
385
386
387
388
389
390
391
392
393
394
395
396
397
398
399
400
401
402
403
404
405
406
407
408
409
410
411
412
413
414
415
416
417
418
419
420
421
422
423
424
425
426
427
428
429
430
431
432
433
434
435
436
437
438
439
440
441
442
443
444
445
446
447
448
449
450
451
452
453
454
455
456
457
458
459
460
461
462
463
464
465
466
467
468
469
470
471
472
473
474
475
476
477
478
479
480
481
482
483
484
485
486
487
488
489
490
491
492
493
494
495
496
497
498
499
500
501
502
503
504
505
506
507
508
509
510
511
512
513
514
515
516
517
518
519
520
521
522
523
524
525
526
527
528
529
530
531
532
533
534
535
536
537
538
539
540
541
542
543
544
545
546
547
548
549
550
551
552
553
554
555
556
557
558
559
560
561
562
563
564
565
566
567
568
569
570
571
572
573
574
575
576
577
578
579
580
581
582
583
584
585
586
587
588
589
590
591
592
593
594
595
596
597
598
599
600
601
602
603
604
605
606
607
608
609
610
611
612
613
614
615
616
617
618
619
620
621
622
623
624
625
626
627
628
629
630
631
632
633
634
635
636
637
638
639
640
641
642
643
644
645
646
647
648
649
650
651
652
653
654
655
656
657
658
659
660
661
662
663
664
665
666
667
668
669
670
671
672
673
674
675
676
677
678
679
680
681
682
683
684
685
686
687
688
689
690
691
692
693
694
695
696
697
698
699
700
701
702
703
704
705
706
707
708
709
710
711
712
713
714
715
716
717
718
719
720
721
722
723
724
725
726
727
728
729
730
731
732
733
734
735
736
737
738
739
740
741
742
743
744
745
746
747
748
749
750
751
752
753
754
755
756
757
758
759
760
761
762
763
764
765
766
767
768
769
770
771
772
773
774
775
776
777
778
779
780
781
782
783
784
785
786
787
788
789
790
791
792
793
794
795
796
797
798
799
800
801
802
803
804
805
806
807
808
809
810
811
812
813
814
815
816
817
818
819
820
821
822
823
824
825
826
827
828
829
830
831
832
833
834
835
836
837
838
839
840
841
842
843
844
845
846
847
848
849
850
851
852
853
854
855
856
857
858
859
860
861
862
863
864
865
866
867
868
869
870
871
872
873
874
875
876
877
878
879
880
881
882
883
884
885
886
887
888
889
890
891
892
893
894
895
896
897
898
899
900
901
902
903
904
905
906
907
908
909
910
911
912
913
914
915
916
917
918
919
920
921
922
923
924
925
926
927
928
929
930
931
932
933
934
935
936
937
938
939
940
941
942
943
944
945
946
947
948
949
950
951
952
953
954
955
956
957
958
959
960
961
962
963
964
965
966
967
968
969
970
971
972
973
974
975
976
977
978
979
980
981
982
983
984
985
986
987
988
989
990
991
992
993
994
995
996
997
998
999
1000
1001
1002
1003
1004
1005
1006
1007
1008
1009
1010
1011
1012
1013
1014
1015
1016
1017
1018
1019
1020
1021
1022
1023
1024
1025
1026
1027
1028
1029
1030
1031
1032
1033
1034
1035
1036
1037
1038
1039
1040
1041
1042
1043
1044
1045
1046
1047
1048
1049
1050
1051
1052
1053
1054
1055
1056
1057
1058
1059
1060
1061
1062
1063
1064
1065
1066
1067
1068
1069
1070
1071
1072
1073
1074
1075
1076
1077
1078
1079
1080
1081
1082
1083
1084
1085
1086
1087
1088
1089
1090
1091
1092
1093
1094
1095
1096
1097
1098
1099
1100
1101
1102
1103
1104
1105
1106
1107
1108
1109
1110
1111
1112
1113
1114
1115
1116
1117
1118
1119
1120
1121
1122
1123
1124
1125
1126
1127
1128
1129
1130
1131
1132
1133
1134
1135
1136
1137
1138
1139
1140
1141
1142
1143
1144
1145
1146
1147
1148
1149
1150
1151
1152
1153
1154
1155
1156
1157
1158
1159
1160
1161
1162
1163
1164
1165
1166
1167
1168
1169
1170
1171
1172
1173
1174
1175
1176
1177
1178
1179
1180
1181
1182
1183
1184
1185
1186
1187
1188
1189
1190
1191
1192
1193
1194
1195
1196
1197
1198
1199
1200
1201
1202
1203
1204
1205
1206
1207
1208
1209
1210
1211
1212
1213
1214
1215
1216
1217
1218
1219
1220
1221
1222
1223
1224
1225
1226
1227
1228
1229
1230
1231
1232
1233
1234
1235
1236
1237
1238
1239
1240
1241
1242
1243
1244
1245
1246
1247
1248
1249
1250
1251
1252
1253
1254
1255
1256
1257
1258
1259
1260
1261
1262
1263
1264
1265
1266
1267
1268
1269
1270
1271
1272
1273
1274
1275
1276
1277
1278
1279
1280
1281
1282
1283
1284
1285
1286
1287
1288
1289
1290
1291
1292
1293
1294
1295
1296
1297
1298
1299
1300
1301
1302
1303
1304
1305
1306
1307
1308
1309
1310
1311
1312
1313
1314
1315
1316
1317
1318
1319
1320
1321
1322
1323
1324
1325
1326
1327
1328
1329
1330
1331
1332
1333
1334
1335
1336
1337
1338
1339
1340
1341
1342
1343
1344
1345
1346
1347
1348
1349
1350
1351
1352
1353
1354
1355
1356
1357
1358
1359
1360
1361
1362
1363
1364
1365
1366
1367
1368
1369
1370
1371
1372
1373
1374
1375
1376
1377
1378
1379
1380
1381
1382
1383
1384
1385
1386
1387
1388
1389
1390
1391
1392
1393
1394
1395
1396
1397
1398
1399
1400
1401
1402
1403
1404
1405
1406
1407
1408
1409
1410
1411
1412
1413
1414
1415
1416
1417
1418
1419
1420
1421
1422
1423
1424
1425
1426
1427
1428
1429
1430
1431
1432
1433
1434
1435
1436
1437
1438
1439
1440
1441
1442
1443
1444
1445
1446
1447
1448
1449
1450
1451
1452
1453
1454
1455
1456
1457
1458
1459
1460
1461
1462
1463
1464
1465
1466
1467
1468
1469
1470
1471
1472
1473
1474
1475
1476
1477
1478
1479
1480
1481
1482
1483
1484
1485
1486
1487
1488
1489
1490
1491
1492
1493
1494
1495
1496
1497
1498
1499
1500
1501
1502
1503
1504
1505
1506
1507
1508
1509
1510
1511
1512
1513
1514
1515
1516
1517
1518
1519
1520
1521
1522
1523
1524
1525
1526
1527
1528
1529
1530
1531
1532
1533
1534
1535
1536
1537
1538
1539
1540
1541
1542
1543
1544
1545
1546
1547
1548
1549
1550
1551
1552
1553
1554
1555
1556
1557
1558
1559
1560
1561
1562
1563
1564
1565
1566
1567
1568
1569
1570
1571
1572
1573
1574
1575
1576
1577
1578
1579
1580
1581
1582
1583
1584
1585
1586
1587
1588
1589
1590
1591
1592
1593
1594
1595
1596
1597
1598
1599
1600
1601
1602
1603
1604
1605
1606
1607
1608
1609
1610
1611
1612
1613
1614
1615
1616
1617
1618
1619
1620
1621
1622
1623
1624
1625
1626
1627
1628
1629
1630
1631
1632
1633
1634
1635
1636
1637
1638
1639
1640
1641
1642
1643
1644
1645
1646
1647
1648
1649
1650
1651
1652
1653
1654
1655
1656
1657
1658
1659
1660
1661
1662
1663
1664
1665
1666
1667
1668
1669
1670
1671
1672
1673
1674
1675
1676
1677
1678
1679
1680
1681
1682
1683
1684
1685
1686
1687
1688
1689
1690
1691
1692
1693
1694
1695
1696
1697
1698
1699
1700
1701
1702
1703
1704
1705
1706
1707
1708
1709
1710
1711
1712
#!/usr/bin/env python
 
'''
EC2 external inventory script
=================================
 
Generates inventory that Ansible can understand by making API request to
AWS EC2 using the Boto library.
 
NOTE: This script assumes Ansible is being executed where the environment
variables needed for Boto have already been set:
    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'
 
Optional region environment variable if region is 'auto'
 
This script also assumes that there is an ec2.ini file alongside it.  To specify a
different path to ec2.ini, define the EC2_INI_PATH environment variable:
 
    export EC2_INI_PATH=/path/to/my_ec2.ini
 
If you're using eucalyptus you need to set the above variables and
you need to define:
 
    export EC2_URL=http://hostname_of_your_cc:port/services/Eucalyptus
 
If you're using boto profiles (requires boto>=2.24.0) you can choose a profile
using the --boto-profile command line argument (e.g. ec2.py --boto-profile prod) or using
the AWS_PROFILE variable:
 
    AWS_PROFILE=prod ansible-playbook -i ec2.py myplaybook.yml
 
For more details, see: http://docs.pythonboto.org/en/latest/boto_config_tut.html
 
You can filter for specific EC2 instances by creating an environment variable
named EC2_INSTANCE_FILTERS, which has the same format as the instance_filters
entry documented in ec2.ini.  For example, to find all hosts whose name begins
with 'webserver', one might use:
 
    export EC2_INSTANCE_FILTERS='tag:Name=webserver*'
 
When run against a specific host, this script returns the following variables:
 - ec2_ami_launch_index
 - ec2_architecture
 - ec2_association
 - ec2_attachTime
 - ec2_attachment
 - ec2_attachmentId
 - ec2_block_devices
 - ec2_client_token
 - ec2_deleteOnTermination
 - ec2_description
 - ec2_deviceIndex
 - ec2_dns_name
 - ec2_eventsSet
 - ec2_group_name
 - ec2_hypervisor
 - ec2_id
 - ec2_image_id
 - ec2_instanceState
 - ec2_instance_type
 - ec2_ipOwnerId
 - ec2_ip_address
 - ec2_item
 - ec2_kernel
 - ec2_key_name
 - ec2_launch_time
 - ec2_monitored
 - ec2_monitoring
 - ec2_networkInterfaceId
 - ec2_ownerId
 - ec2_persistent
 - ec2_placement
 - ec2_platform
 - ec2_previous_state
 - ec2_private_dns_name
 - ec2_private_ip_address
 - ec2_publicIp
 - ec2_public_dns_name
 - ec2_ramdisk
 - ec2_reason
 - ec2_region
 - ec2_requester_id
 - ec2_root_device_name
 - ec2_root_device_type
 - ec2_security_group_ids
 - ec2_security_group_names
 - ec2_shutdown_state
 - ec2_sourceDestCheck
 - ec2_spot_instance_request_id
 - ec2_state
 - ec2_state_code
 - ec2_state_reason
 - ec2_status
 - ec2_subnet_id
 - ec2_tenancy
 - ec2_virtualization_type
 - ec2_vpc_id
 
These variables are pulled out of a boto.ec2.instance object. There is a lack of
consistency with variable spellings (camelCase and underscores) since this
just loops through all variables the object exposes. It is preferred to use the
ones with underscores when multiple exist.
 
In addition, if an instance has AWS tags associated with it, each tag is a new
variable named:
 - ec2_tag_[Key] = [Value]
 
Security groups are comma-separated in 'ec2_security_group_ids' and
'ec2_security_group_names'.
 
When destination_format and destination_format_tags are specified
the destination_format can be built from the instance tags and attributes.
The behavior will first check the user defined tags, then proceed to
check instance attributes, and finally if neither are found 'nil' will
be used instead.
 
'my_instance': {
    'region': 'us-east-1',             # attribute
    'availability_zone': 'us-east-1a', # attribute
    'private_dns_name': '172.31.0.1',  # attribute
    'ec2_tag_deployment': 'blue',      # tag
    'ec2_tag_clusterid': 'ansible',    # tag
    'ec2_tag_Name': 'webserver',       # tag
    ...
}
 
Inside of the ec2.ini file the following settings are specified:
...
destination_format: {0}-{1}-{2}-{3}
destination_format_tags: Name,clusterid,deployment,private_dns_name
...
 
These settings would produce a destination_format as the following:
'webserver-ansible-blue-172.31.0.1'
'''
 
# (c) 2012, Peter Sankauskas
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
 
######################################################################
 
import sys
import os
import argparse
import re
from time import time
from copy import deepcopy
from datetime import date, datetime
import boto
from boto import ec2
from boto import rds
from boto import elasticache
from boto import route53
from boto import sts
 
from ansible.module_utils import six
from ansible.module_utils import ec2 as ec2_utils
from ansible.module_utils.six.moves import configparser
 
HAS_BOTO3 = False
try:
    import boto3  # noqa
    HAS_BOTO3 = True
except ImportError:
    pass
 
from collections import defaultdict
 
import json
 
DEFAULTS = {
    'all_elasticache_clusters': 'False',
    'all_elasticache_nodes': 'False',
    'all_elasticache_replication_groups': 'False',
    'all_instances': 'False',
    'all_rds_instances': 'False',
    'aws_access_key_id': '',
    'aws_secret_access_key': '',
    'aws_security_token': '',
    'boto_profile': '',
    'cache_max_age': '300',
    'cache_path': '~/.ansible/tmp',
    'destination_variable': 'public_dns_name',
    'elasticache': 'True',
    'eucalyptus': 'False',
    'eucalyptus_host': '',
    'expand_csv_tags': 'False',
    'group_by_ami_id': 'True',
    'group_by_availability_zone': 'True',
    'group_by_aws_account': 'False',
    'group_by_elasticache_cluster': 'True',
    'group_by_elasticache_engine': 'True',
    'group_by_elasticache_parameter_group': 'True',
    'group_by_elasticache_replication_group': 'True',
    'group_by_instance_id': 'True',
    'group_by_instance_state': 'False',
    'group_by_instance_type': 'True',
    'group_by_key_pair': 'True',
    'group_by_platform': 'True',
    'group_by_rds_engine': 'True',
    'group_by_rds_parameter_group': 'True',
    'group_by_region': 'True',
    'group_by_route53_names': 'True',
    'group_by_security_group': 'True',
    'group_by_tag_keys': 'True',
    'group_by_tag_none': 'True',
    'group_by_vpc_id': 'True',
    'hostname_variable': '',
    'iam_role': '',
    'include_rds_clusters': 'False',
    'nested_groups': 'False',
    'pattern_exclude': '',
    'pattern_include': '',
    'rds': 'False',
    'regions': 'all',
    'regions_exclude': 'us-gov-west-1, cn-north-1',
    'replace_dash_in_groups': 'True',
    'route53': 'False',
    'route53_excluded_zones': '',
    'route53_hostnames': '',
    'stack_filters': 'False',
    'vpc_destination_variable': 'ip_address'
}
 
 
class Ec2Inventory(object):
 
    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}
 
    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
 
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
 
    def __init__(self):
        ''' Main execution path '''
 
        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = self._empty_inventory()
 
        self.aws_account_id = None
 
        # Index of hostname (address) to instance ID
        self.index = {}
 
        # Boto profile to use (if any)
        self.boto_profile = None
 
        # AWS credentials.
        self.credentials = {}
 
        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.read_settings()
 
        # Make sure that profile_name is not passed at all if not set
        # as pre 2.24 boto will fall over otherwise
        if self.boto_profile:
            if not hasattr(boto.ec2.EC2Connection, 'profile_name'):
                self.fail_with_error("boto version must be >= 2.24 to use profile")
 
        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()
 
        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()
 
        elif self.args.list:
            # Display list of instances for inventory
            if self.inventory == self._empty_inventory():
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)
 
        print(data_to_print)
 
    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''
 
        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True
 
        return False
 
    def read_settings(self):
        ''' Reads the settings from the ec2.ini file '''
 
        scriptbasename = __file__
        scriptbasename = os.path.basename(scriptbasename)
        scriptbasename = scriptbasename.replace('.py', '')
 
        defaults = {
            'ec2': {
                'ini_fallback': os.path.join(os.path.dirname(__file__), 'ec2.ini'),
                'ini_path': os.path.join(os.path.dirname(__file__), '%s.ini' % scriptbasename)
            }
        }
 
        if six.PY3:
            config = configparser.ConfigParser(DEFAULTS)
        else:
            config = configparser.SafeConfigParser(DEFAULTS)
        ec2_ini_path = os.environ.get('EC2_INI_PATH', defaults['ec2']['ini_path'])
        ec2_ini_path = os.path.expanduser(os.path.expandvars(ec2_ini_path))
 
        if not os.path.isfile(ec2_ini_path):
            ec2_ini_path = os.path.expanduser(defaults['ec2']['ini_fallback'])
 
        if os.path.isfile(ec2_ini_path):
            config.read(ec2_ini_path)
 
        # Add empty sections if they don't exist
        try:
            config.add_section('ec2')
        except configparser.DuplicateSectionError:
            pass
 
        try:
            config.add_section('credentials')
        except configparser.DuplicateSectionError:
            pass
 
        # is eucalyptus?
        self.eucalyptus = config.getboolean('ec2', 'eucalyptus')
        self.eucalyptus_host = config.get('ec2', 'eucalyptus_host')
 
        # Regions
        self.regions = []
        config_regions = config.get('ec2', 'regions')
        if (config_regions == 'all'):
            if self.eucalyptus_host:
                self.regions.append(boto.connect_euca(host=self.eucalyptus_host).region.name, **self.credentials)
            else:
                config_regions_exclude = config.get('ec2', 'regions_exclude')
 
                for region_info in ec2.regions():
                    if region_info.name not in config_regions_exclude:
                        self.regions.append(region_info.name)
        else:
            self.regions = config_regions.split(",")
        if 'auto' in self.regions:
            env_region = os.environ.get('AWS_REGION')
            if env_region is None:
                env_region = os.environ.get('AWS_DEFAULT_REGION')
            self.regions = [env_region]
 
        # Destination addresses
        self.destination_variable = config.get('ec2', 'destination_variable')
        self.vpc_destination_variable = config.get('ec2', 'vpc_destination_variable')
        self.hostname_variable = config.get('ec2', 'hostname_variable')
 
        if config.has_option('ec2', 'destination_format') and \
           config.has_option('ec2', 'destination_format_tags'):
            self.destination_format = config.get('ec2', 'destination_format')
            self.destination_format_tags = config.get('ec2', 'destination_format_tags').split(',')
        else:
            self.destination_format = None
            self.destination_format_tags = None
 
        # Route53
        self.route53_enabled = config.getboolean('ec2', 'route53')
        self.route53_hostnames = config.get('ec2', 'route53_hostnames')
 
        self.route53_excluded_zones = []
        self.route53_excluded_zones = [a for a in config.get('ec2', 'route53_excluded_zones').split(',') if a]
 
        # Include RDS instances?
        self.rds_enabled = config.getboolean('ec2', 'rds')
 
        # Include RDS cluster instances?
        self.include_rds_clusters = config.getboolean('ec2', 'include_rds_clusters')
 
        # Include ElastiCache instances?
        self.elasticache_enabled = config.getboolean('ec2', 'elasticache')
 
        # Return all EC2 instances?
        self.all_instances = config.getboolean('ec2', 'all_instances')
 
        # Instance states to be gathered in inventory. Default is 'running'.
        # Setting 'all_instances' to 'yes' overrides this option.
        ec2_valid_instance_states = [
            'pending',
            'running',
            'shutting-down',
            'terminated',
            'stopping',
            'stopped'
        ]
        self.ec2_instance_states = []
        if self.all_instances:
            self.ec2_instance_states = ec2_valid_instance_states
        elif config.has_option('ec2', 'instance_states'):
            for instance_state in config.get('ec2', 'instance_states').split(','):
                instance_state = instance_state.strip()
                if instance_state not in ec2_valid_instance_states:
                    continue
                self.ec2_instance_states.append(instance_state)
        else:
            self.ec2_instance_states = ['running']
 
        # Return all RDS instances? (if RDS is enabled)
        self.all_rds_instances = config.getboolean('ec2', 'all_rds_instances')
 
        # Return all ElastiCache replication groups? (if ElastiCache is enabled)
        self.all_elasticache_replication_groups = config.getboolean('ec2', 'all_elasticache_replication_groups')
 
        # Return all ElastiCache clusters? (if ElastiCache is enabled)
        self.all_elasticache_clusters = config.getboolean('ec2', 'all_elasticache_clusters')
 
        # Return all ElastiCache nodes? (if ElastiCache is enabled)
        self.all_elasticache_nodes = config.getboolean('ec2', 'all_elasticache_nodes')
 
        # boto configuration profile (prefer CLI argument then environment variables then config file)
        self.boto_profile = self.args.boto_profile or \
            os.environ.get('AWS_PROFILE') or \
            config.get('ec2', 'boto_profile')
 
        # AWS credentials (prefer environment variables)
        if not (self.boto_profile or os.environ.get('AWS_ACCESS_KEY_ID') or
                os.environ.get('AWS_PROFILE')):
 
            aws_access_key_id = config.get('credentials', 'aws_access_key_id')
            aws_secret_access_key = config.get('credentials', 'aws_secret_access_key')
            aws_security_token = config.get('credentials', 'aws_security_token')
 
            if aws_access_key_id:
                self.credentials = {
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                }
                if aws_security_token:
                    self.credentials['security_token'] = aws_security_token
 
        # Cache related
        cache_dir = os.path.expanduser(config.get('ec2', 'cache_path'))
        if self.boto_profile:
            cache_dir = os.path.join(cache_dir, 'profile_' + self.boto_profile)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
 
        cache_name = 'ansible-ec2'
        cache_id = self.boto_profile or os.environ.get('AWS_ACCESS_KEY_ID', self.credentials.get('aws_access_key_id'))
        if cache_id:
            cache_name = '%s-%s' % (cache_name, cache_id)
        cache_name += '-' + str(abs(hash(__file__)))[1:7]
        self.cache_path_cache = os.path.join(cache_dir, "%s.cache" % cache_name)
        self.cache_path_index = os.path.join(cache_dir, "%s.index" % cache_name)
        self.cache_max_age = config.getint('ec2', 'cache_max_age')
 
        self.expand_csv_tags = config.getboolean('ec2', 'expand_csv_tags')
 
        # Configure nested groups instead of flat namespace.
        self.nested_groups = config.getboolean('ec2', 'nested_groups')
 
        # Replace dash or not in group names
        self.replace_dash_in_groups = config.getboolean('ec2', 'replace_dash_in_groups')
 
        # IAM role to assume for connection
        self.iam_role = config.get('ec2', 'iam_role')
 
        # Configure which groups should be created.
 
        group_by_options = [a for a in DEFAULTS if a.startswith('group_by')]
        for option in group_by_options:
            setattr(self, option, config.getboolean('ec2', option))
 
        # Do we need to just include hosts that match a pattern?
        self.pattern_include = config.get('ec2', 'pattern_include')
        if self.pattern_include:
            self.pattern_include = re.compile(self.pattern_include)
 
        # Do we need to exclude hosts that match a pattern?
        self.pattern_exclude = config.get('ec2', 'pattern_exclude')
        if self.pattern_exclude:
            self.pattern_exclude = re.compile(self.pattern_exclude)
 
        # Do we want to stack multiple filters?
        self.stack_filters = config.getboolean('ec2', 'stack_filters')
 
        # Instance filters (see boto and EC2 API docs). Ignore invalid filters.
        self.ec2_instance_filters = []
 
        if config.has_option('ec2', 'instance_filters') or 'EC2_INSTANCE_FILTERS' in os.environ:
            filters = os.getenv('EC2_INSTANCE_FILTERS', config.get('ec2', 'instance_filters') if config.has_option('ec2', 'instance_filters') else '')
 
            if self.stack_filters and '&' in filters:
                self.fail_with_error("AND filters along with stack_filter enabled is not supported.\n")
 
            filter_sets = [f for f in filters.split(',') if f]
 
            for filter_set in filter_sets:
                filters = {}
                filter_set = filter_set.strip()
                for instance_filter in filter_set.split("&"):
                    instance_filter = instance_filter.strip()
                    if not instance_filter or '=' not in instance_filter:
                        continue
                    filter_key, filter_value = [x.strip() for x in instance_filter.split('=', 1)]
                    if not filter_key:
                        continue
                    filters[filter_key] = filter_value
                self.ec2_instance_filters.append(filters.copy())
 
    def parse_cli_args(self):
        ''' Command line argument processing '''
 
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on EC2')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to EC2 (default: False - use cache files)')
        parser.add_argument('--profile', '--boto-profile', action='store', dest='boto_profile',
                            help='Use boto profile for connections to EC2')
        self.args = parser.parse_args()
 
    def do_api_calls_update_cache(self):
        ''' Do API calls to each region, and save data in cache files '''
 
        if self.route53_enabled:
            self.get_route53_records()
 
        for region in self.regions:
            self.get_instances_by_region(region)
            if self.rds_enabled:
                self.get_rds_instances_by_region(region)
            if self.elasticache_enabled:
                self.get_elasticache_clusters_by_region(region)
                self.get_elasticache_replication_groups_by_region(region)
            if self.include_rds_clusters:
                self.include_rds_clusters_by_region(region)
 
        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)
 
    def connect(self, region):
        ''' create connection to api server'''
        if self.eucalyptus:
            conn = boto.connect_euca(host=self.eucalyptus_host, **self.credentials)
            conn.APIVersion = '2010-08-31'
        else:
            conn = self.connect_to_aws(ec2, region)
        return conn
 
    def boto_fix_security_token_in_profile(self, connect_args):
        ''' monkey patch for boto issue boto/boto#2100 '''
        profile = 'profile ' + self.boto_profile
        if boto.config.has_option(profile, 'aws_security_token'):
            connect_args['security_token'] = boto.config.get(profile, 'aws_security_token')
        return connect_args
 
    def connect_to_aws(self, module, region):
        connect_args = deepcopy(self.credentials)
 
        # only pass the profile name if it's set (as it is not supported by older boto versions)
        if self.boto_profile:
            connect_args['profile_name'] = self.boto_profile
            self.boto_fix_security_token_in_profile(connect_args)
        elif os.environ.get('AWS_SESSION_TOKEN'):
            connect_args['security_token'] = os.environ.get('AWS_SESSION_TOKEN')
 
        if self.iam_role:
            sts_conn = sts.connect_to_region(region, **connect_args)
            role = sts_conn.assume_role(self.iam_role, 'ansible_dynamic_inventory')
            connect_args['aws_access_key_id'] = role.credentials.access_key
            connect_args['aws_secret_access_key'] = role.credentials.secret_key
            connect_args['security_token'] = role.credentials.session_token
 
        conn = module.connect_to_region(region, **connect_args)
        # connect_to_region will fail "silently" by returning None if the region name is wrong or not supported
        if conn is None:
            self.fail_with_error("region name: %s likely not supported, or AWS is down.  connection to region failed." % region)
        return conn
 
    def get_instances_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of instances in a particular
        region '''
 
        try:
            conn = self.connect(region)
            reservations = []
            if self.ec2_instance_filters:
                if self.stack_filters:
                    filters_dict = {}
                    for filters in self.ec2_instance_filters:
                        filters_dict.update(filters)
                    reservations.extend(conn.get_all_instances(filters=filters_dict))
                else:
                    for filters in self.ec2_instance_filters:
                        reservations.extend(conn.get_all_instances(filters=filters))
            else:
                reservations = conn.get_all_instances()
 
            # Pull the tags back in a second step
            # AWS are on record as saying that the tags fetched in the first `get_all_instances` request are not
            # reliable and may be missing, and the only way to guarantee they are there is by calling `get_all_tags`
            instance_ids = []
            for reservation in reservations:
                instance_ids.extend([instance.id for instance in reservation.instances])
 
            max_filter_value = 199
            tags = []
            for i in range(0, len(instance_ids), max_filter_value):
                tags.extend(conn.get_all_tags(filters={'resource-type': 'instance', 'resource-id': instance_ids[i:i + max_filter_value]}))
 
            tags_by_instance_id = defaultdict(dict)
            for tag in tags:
                tags_by_instance_id[tag.res_id][tag.name] = tag.value
 
            if (not self.aws_account_id) and reservations:
                self.aws_account_id = reservations[0].owner_id
 
            for reservation in reservations:
                for instance in reservation.instances:
                    instance.tags = tags_by_instance_id[instance.id]
                    self.add_instance(instance, region)
 
        except boto.exception.BotoServerError as e:
            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            else:
                backend = 'Eucalyptus' if self.eucalyptus else 'AWS'
                error = "Error connecting to %s backend.\n%s" % (backend, e.message)
            self.fail_with_error(error, 'getting EC2 instances')
 
    def tags_match_filters(self, tags):
        ''' return True if given tags match configured filters '''
        if not self.ec2_instance_filters:
            return True
 
        for filters in self.ec2_instance_filters:
            for filter_name, filter_value in filters.items():
                if filter_name[:4] != 'tag:':
                    continue
                filter_name = filter_name[4:]
                if filter_name not in tags:
                    if self.stack_filters:
                        return False
                    continue
                if isinstance(filter_value, list):
                    if self.stack_filters and tags[filter_name] not in filter_value:
                        return False
                    if not self.stack_filters and tags[filter_name] in filter_value:
                        return True
                if isinstance(filter_value, six.string_types):
                    if self.stack_filters and tags[filter_name] != filter_value:
                        return False
                    if not self.stack_filters and tags[filter_name] == filter_value:
                        return True
 
        return self.stack_filters
 
    def get_rds_instances_by_region(self, region):
        ''' Makes an AWS API call to the list of RDS instances in a particular
        region '''
 
        if not HAS_BOTO3:
            self.fail_with_error("Working with RDS instances requires boto3 - please install boto3 and try again",
                                 "getting RDS instances")
 
        client = ec2_utils.boto3_inventory_conn('client', 'rds', region, **self.credentials)
        db_instances = client.describe_db_instances()
 
        try:
            conn = self.connect_to_aws(rds, region)
            if conn:
                marker = None
                while True:
                    instances = conn.get_all_dbinstances(marker=marker)
                    marker = instances.marker
                    for index, instance in enumerate(instances):
                        # Add tags to instances.
                        instance.arn = db_instances['DBInstances'][index]['DBInstanceArn']
                        tags = client.list_tags_for_resource(ResourceName=instance.arn)['TagList']
                        instance.tags = {}
                        for tag in tags:
                            instance.tags[tag['Key']] = tag['Value']
                        if self.tags_match_filters(instance.tags):
                            self.add_rds_instance(instance, region)
                    if not marker:
                        break
        except boto.exception.BotoServerError as e:
            error = e.reason
 
            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            elif e.error_code == "OptInRequired":
                error = "RDS hasn't been enabled for this account yet. " \
                    "You must either log in to the RDS service through the AWS console to enable it, " \
                    "or set 'rds = False' in ec2.ini"
            elif not e.reason == "Forbidden":
                error = "Looks like AWS RDS is down:\n%s" % e.message
            self.fail_with_error(error, 'getting RDS instances')
 
    def include_rds_clusters_by_region(self, region):
        if not HAS_BOTO3:
            self.fail_with_error("Working with RDS clusters requires boto3 - please install boto3 and try again",
                                 "getting RDS clusters")
 
        client = ec2_utils.boto3_inventory_conn('client', 'rds', region, **self.credentials)
 
        marker, clusters = '', []
        while marker is not None:
            resp = client.describe_db_clusters(Marker=marker)
            clusters.extend(resp["DBClusters"])
            marker = resp.get('Marker', None)
 
        account_id = boto.connect_iam().get_user().arn.split(':')[4]
        c_dict = {}
        for c in clusters:
            if not self.ec2_instance_filters:
                matches_filter = True
            else:
                matches_filter = False
 
            try:
                # arn:aws:rds:<region>:<account number>:<resourcetype>:<name>
                tags = client.list_tags_for_resource(
                    ResourceName='arn:aws:rds:' + region + ':' + account_id + ':cluster:' + c['DBClusterIdentifier'])
                c['Tags'] = tags['TagList']
 
                if self.ec2_instance_filters:
                    for filters in self.ec2_instance_filters:
                        for filter_key, filter_values in filters.items():
                            # get AWS tag key e.g. tag:env will be 'env'
                            tag_name = filter_key.split(":", 1)[1]
                            # Filter values is a list (if you put multiple values for the same tag name)
                            matches_filter = any(d['Key'] == tag_name and d['Value'] in filter_values for d in c['Tags'])
 
                            if matches_filter:
                                # it matches a filter, so stop looking for further matches
                                break
 
                        if matches_filter:
                            break
 
            except Exception as e:
                if e.message.find('DBInstanceNotFound') >= 0:
                    # AWS RDS bug (2016-01-06) means deletion does not fully complete and leave an 'empty' cluster.
                    # Ignore errors when trying to find tags for these
                    pass
 
            # ignore empty clusters caused by AWS bug
            if len(c['DBClusterMembers']) == 0:
                continue
            elif matches_filter:
                c_dict[c['DBClusterIdentifier']] = c
 
        self.inventory['db_clusters'] = c_dict
 
    def get_elasticache_clusters_by_region(self, region):
        ''' Makes an AWS API call to the list of ElastiCache clusters (with
        nodes' info) in a particular region.'''
 
        # ElastiCache boto module doesn't provide a get_all_instances method,
        # that's why we need to call describe directly (it would be called by
        # the shorthand method anyway...)
        clusters = []
        try:
            conn = self.connect_to_aws(elasticache, region)
            if conn:
                # show_cache_node_info = True
                # because we also want nodes' information
                _marker = 1
                while _marker:
                    if _marker == 1:
                        _marker = None
                    response = conn.describe_cache_clusters(None, None, _marker, True)
                    _marker = response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['Marker']
                    try:
                        # Boto also doesn't provide wrapper classes to CacheClusters or
                        # CacheNodes. Because of that we can't make use of the get_list
                        # method in the AWSQueryConnection. Let's do the work manually
                        clusters = clusters + response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters']
                    except KeyError as e:
                        error = "ElastiCache query to AWS failed (unexpected format)."
                        self.fail_with_error(error, 'getting ElastiCache clusters')
        except boto.exception.BotoServerError as e:
            error = e.reason
 
            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            elif e.error_code == "OptInRequired":
                error = "ElastiCache hasn't been enabled for this account yet. " \
                    "You must either log in to the ElastiCache service through the AWS console to enable it, " \
                    "or set 'elasticache = False' in ec2.ini"
            elif not e.reason == "Forbidden":
                error = "Looks like AWS ElastiCache is down:\n%s" % e.message
            self.fail_with_error(error, 'getting ElastiCache clusters')
 
        for cluster in clusters:
            self.add_elasticache_cluster(cluster, region)
 
    def get_elasticache_replication_groups_by_region(self, region):
        ''' Makes an AWS API call to the list of ElastiCache replication groups
        in a particular region.'''
 
        # ElastiCache boto module doesn't provide a get_all_instances method,
        # that's why we need to call describe directly (it would be called by
        # the shorthand method anyway...)
        try:
            conn = self.connect_to_aws(elasticache, region)
            if conn:
                response = conn.describe_replication_groups()
 
        except boto.exception.BotoServerError as e:
            error = e.reason
 
            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            if not e.reason == "Forbidden":
                error = "Looks like AWS ElastiCache [Replication Groups] is down:\n%s" % e.message
            self.fail_with_error(error, 'getting ElastiCache clusters')
 
        try:
            # Boto also doesn't provide wrapper classes to ReplicationGroups
            # Because of that we can't make use of the get_list method in the
            # AWSQueryConnection. Let's do the work manually
            replication_groups = response['DescribeReplicationGroupsResponse']['DescribeReplicationGroupsResult']['ReplicationGroups']
 
        except KeyError as e:
            error = "ElastiCache [Replication Groups] query to AWS failed (unexpected format)."
            self.fail_with_error(error, 'getting ElastiCache clusters')
 
        for replication_group in replication_groups:
            self.add_elasticache_replication_group(replication_group, region)
 
    def get_auth_error_message(self):
        ''' create an informative error message if there is an issue authenticating'''
        errors = ["Authentication error retrieving ec2 inventory."]
        if None in [os.environ.get('AWS_ACCESS_KEY_ID'), os.environ.get('AWS_SECRET_ACCESS_KEY')]:
            errors.append(' - No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY environment vars found')
        else:
            errors.append(' - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment vars found but may not be correct')
 
        boto_paths = ['/etc/boto.cfg', '~/.boto', '~/.aws/credentials']
        boto_config_found = [p for p in boto_paths if os.path.isfile(os.path.expanduser(p))]
        if len(boto_config_found) > 0:
            errors.append(" - Boto configs found at '%s', but the credentials contained may not be correct" % ', '.join(boto_config_found))
        else:
            errors.append(" - No Boto config found at any expected location '%s'" % ', '.join(boto_paths))
 
        return '\n'.join(errors)
 
    def fail_with_error(self, err_msg, err_operation=None):
        '''log an error to std err for ansible-playbook to consume and exit'''
        if err_operation:
            err_msg = 'ERROR: "{err_msg}", while: {err_operation}'.format(
                err_msg=err_msg, err_operation=err_operation)
        sys.stderr.write(err_msg)
        sys.exit(1)
 
    def get_instance(self, region, instance_id):
        conn = self.connect(region)
 
        reservations = conn.get_all_instances([instance_id])
        for reservation in reservations:
            for instance in reservation.instances:
                return instance
 
    def add_instance(self, instance, region):
        ''' Adds an instance to the inventory and index, as long as it is
        addressable '''
 
        # Only return instances with desired instance states
        if instance.state not in self.ec2_instance_states:
            return
 
        # Select the best destination address
        # When destination_format and destination_format_tags are specified
        # the following code will attempt to find the instance tags first,
        # then the instance attributes next, and finally if neither are found
        # assign nil for the desired destination format attribute.
        if self.destination_format and self.destination_format_tags:
            dest_vars = []
            inst_tags = getattr(instance, 'tags')
            for tag in self.destination_format_tags:
                if tag in inst_tags:
                    dest_vars.append(inst_tags[tag])
                elif hasattr(instance, tag):
                    dest_vars.append(getattr(instance, tag))
                else:
                    dest_vars.append('nil')
 
            dest = self.destination_format.format(*dest_vars)
        elif instance.subnet_id:
            dest = getattr(instance, self.vpc_destination_variable, None)
            if dest is None:
                dest = getattr(instance, 'tags').get(self.vpc_destination_variable, None)
        else:
            dest = getattr(instance, self.destination_variable, None)
            if dest is None:
                dest = getattr(instance, 'tags').get(self.destination_variable, None)
 
        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return
 
        # Set the inventory name
        hostname = None
        if self.hostname_variable:
            if self.hostname_variable.startswith('tag_'):
                hostname = instance.tags.get(self.hostname_variable[4:], None)
            else:
                hostname = getattr(instance, self.hostname_variable)
 
        # set the hostname from route53
        if self.route53_enabled and self.route53_hostnames:
            route53_names = self.get_instance_route53_names(instance)
            for name in route53_names:
                if name.endswith(self.route53_hostnames):
                    hostname = name
 
        # If we can't get a nice hostname, use the destination address
        if not hostname:
            hostname = dest
        # to_safe strips hostname characters like dots, so don't strip route53 hostnames
        elif self.route53_enabled and self.route53_hostnames and hostname.endswith(self.route53_hostnames):
            hostname = hostname.lower()
        else:
            hostname = self.to_safe(hostname).lower()
 
        # if we only want to include hosts that match a pattern, skip those that don't
        if self.pattern_include and not self.pattern_include.match(hostname):
            return
 
        # if we need to exclude hosts that match a pattern, skip those
        if self.pattern_exclude and self.pattern_exclude.match(hostname):
            return
 
        # Add to index
        self.index[hostname] = [region, instance.id]
 
        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[instance.id] = [hostname]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', instance.id)
 
        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)
 
        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, instance.placement, hostname)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, instance.placement)
                self.push_group(self.inventory, 'zones', instance.placement)
 
        # Inventory: Group by Amazon Machine Image (AMI) ID
        if self.group_by_ami_id:
            ami_id = self.to_safe(instance.image_id)
            self.push(self.inventory, ami_id, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'images', ami_id)
 
        # Inventory: Group by instance type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + instance.instance_type)
            self.push(self.inventory, type_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)
 
        # Inventory: Group by instance state
        if self.group_by_instance_state:
            state_name = self.to_safe('instance_state_' + instance.state)
            self.push(self.inventory, state_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'instance_states', state_name)
 
        # Inventory: Group by platform
        if self.group_by_platform:
            if instance.platform:
                platform = self.to_safe('platform_' + instance.platform)
            else:
                platform = self.to_safe('platform_undefined')
            self.push(self.inventory, platform, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'platforms', platform)
 
        # Inventory: Group by key pair
        if self.group_by_key_pair and instance.key_name:
            key_name = self.to_safe('key_' + instance.key_name)
            self.push(self.inventory, key_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'keys', key_name)
 
        # Inventory: Group by VPC
        if self.group_by_vpc_id and instance.vpc_id:
            vpc_id_name = self.to_safe('vpc_id_' + instance.vpc_id)
            self.push(self.inventory, vpc_id_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'vpcs', vpc_id_name)
 
        # Inventory: Group by security group
        if self.group_by_security_group:
            try:
                for group in instance.groups:
                    key = self.to_safe("security_group_" + group.name)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)
            except AttributeError:
                self.fail_with_error('\n'.join(['Package boto seems a bit older.',
                                                'Please upgrade boto >= 2.3.0.']))
 
        # Inventory: Group by AWS account ID
        if self.group_by_aws_account:
            self.push(self.inventory, self.aws_account_id, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'accounts', self.aws_account_id)
 
        # Inventory: Group by tag keys
        if self.group_by_tag_keys:
            for k, v in instance.tags.items():
                if self.expand_csv_tags and v and ',' in v:
                    values = map(lambda x: x.strip(), v.split(','))
                else:
                    values = [v]
 
                for v in values:
                    if v:
                        key = self.to_safe("tag_" + k + "=" + v)
                    else:
                        key = self.to_safe("tag_" + k)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))
                        if v:
                            self.push_group(self.inventory, self.to_safe("tag_" + k), key)
 
        # Inventory: Group by Route53 domain names if enabled
        if self.route53_enabled and self.group_by_route53_names:
            route53_names = self.get_instance_route53_names(instance)
            for name in route53_names:
                self.push(self.inventory, name, hostname)
                if self.nested_groups:
                    self.push_group(self.inventory, 'route53', name)
 
        # Global Tag: instances without tags
        if self.group_by_tag_none and len(instance.tags) == 0:
            self.push(self.inventory, 'tag_none', hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', 'tag_none')
 
        # Global Tag: tag all EC2 instances
        self.push(self.inventory, 'ec2', hostname)
 
        self.inventory["_meta"]["hostvars"][hostname] = self.get_host_info_dict_from_instance(instance)
        self.inventory["_meta"]["hostvars"][hostname]['ansible_host'] = dest
 
    def add_rds_instance(self, instance, region):
        ''' Adds an RDS instance to the inventory and index, as long as it is
        addressable '''
 
        # Only want available instances unless all_rds_instances is True
        if not self.all_rds_instances and instance.status != 'available':
            return
 
        # Select the best destination address
        dest = instance.endpoint[0]
 
        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return
 
        # Set the inventory name
        hostname = None
        if self.hostname_variable:
            if self.hostname_variable.startswith('tag_'):
                hostname = instance.tags.get(self.hostname_variable[4:], None)
            else:
                hostname = getattr(instance, self.hostname_variable)
 
        # If we can't get a nice hostname, use the destination address
        if not hostname:
            hostname = dest
 
        hostname = self.to_safe(hostname).lower()
 
        # Add to index
        self.index[hostname] = [region, instance.id]
 
        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[instance.id] = [hostname]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', instance.id)
 
        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)
 
        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, instance.availability_zone, hostname)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, instance.availability_zone)
                self.push_group(self.inventory, 'zones', instance.availability_zone)
 
        # Inventory: Group by instance type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + instance.instance_class)
            self.push(self.inventory, type_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)
 
        # Inventory: Group by VPC
        if self.group_by_vpc_id and instance.subnet_group and instance.subnet_group.vpc_id:
            vpc_id_name = self.to_safe('vpc_id_' + instance.subnet_group.vpc_id)
            self.push(self.inventory, vpc_id_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'vpcs', vpc_id_name)
 
        # Inventory: Group by security group
        if self.group_by_security_group:
            try:
                if instance.security_group:
                    key = self.to_safe("security_group_" + instance.security_group.name)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)
 
            except AttributeError:
                self.fail_with_error('\n'.join(['Package boto seems a bit older.',
                                                'Please upgrade boto >= 2.3.0.']))
        # Inventory: Group by tag keys
        if self.group_by_tag_keys:
            for k, v in instance.tags.items():
                if self.expand_csv_tags and v and ',' in v:
                    values = map(lambda x: x.strip(), v.split(','))
                else:
                    values = [v]
 
                for v in values:
                    if v:
                        key = self.to_safe("tag_" + k + "=" + v)
                    else:
                        key = self.to_safe("tag_" + k)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))
                        if v:
                            self.push_group(self.inventory, self.to_safe("tag_" + k), key)
 
        # Inventory: Group by engine
        if self.group_by_rds_engine:
            self.push(self.inventory, self.to_safe("rds_" + instance.engine), hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'rds_engines', self.to_safe("rds_" + instance.engine))
 
        # Inventory: Group by parameter group
        if self.group_by_rds_parameter_group:
            self.push(self.inventory, self.to_safe("rds_parameter_group_" + instance.parameter_group.name), hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'rds_parameter_groups', self.to_safe("rds_parameter_group_" + instance.parameter_group.name))
 
        # Global Tag: instances without tags
        if self.group_by_tag_none and len(instance.tags) == 0:
            self.push(self.inventory, 'tag_none', hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', 'tag_none')
 
        # Global Tag: all RDS instances
        self.push(self.inventory, 'rds', hostname)
 
        self.inventory["_meta"]["hostvars"][hostname] = self.get_host_info_dict_from_instance(instance)
        self.inventory["_meta"]["hostvars"][hostname]['ansible_host'] = dest
 
    def add_elasticache_cluster(self, cluster, region):
        ''' Adds an ElastiCache cluster to the inventory and index, as long as
        it's nodes are addressable '''
 
        # Only want available clusters unless all_elasticache_clusters is True
        if not self.all_elasticache_clusters and cluster['CacheClusterStatus'] != 'available':
            return
 
        # Select the best destination address
        if 'ConfigurationEndpoint' in cluster and cluster['ConfigurationEndpoint']:
            # Memcached cluster
            dest = cluster['ConfigurationEndpoint']['Address']
            is_redis = False
        else:
            # Redis sigle node cluster
            # Because all Redis clusters are single nodes, we'll merge the
            # info from the cluster with info about the node
            dest = cluster['CacheNodes'][0]['Endpoint']['Address']
            is_redis = True
 
        if not dest:
            # Skip clusters we cannot address (e.g. private VPC subnet)
            return
 
        # Add to index
        self.index[dest] = [region, cluster['CacheClusterId']]
 
        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[cluster['CacheClusterId']] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', cluster['CacheClusterId'])
 
        # Inventory: Group by region
        if self.group_by_region and not is_redis:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)
 
        # Inventory: Group by availability zone
        if self.group_by_availability_zone and not is_redis:
            self.push(self.inventory, cluster['PreferredAvailabilityZone'], dest)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, cluster['PreferredAvailabilityZone'])
                self.push_group(self.inventory, 'zones', cluster['PreferredAvailabilityZone'])
 
        # Inventory: Group by node type
        if self.group_by_instance_type and not is_redis:
            type_name = self.to_safe('type_' + cluster['CacheNodeType'])
            self.push(self.inventory, type_name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)
 
        # Inventory: Group by VPC (information not available in the current
        # AWS API version for ElastiCache)
 
        # Inventory: Group by security group
        if self.group_by_security_group and not is_redis:
 
            # Check for the existence of the 'SecurityGroups' key and also if
            # this key has some value. When the cluster is not placed in a SG
            # the query can return None here and cause an error.
            if 'SecurityGroups' in cluster and cluster['SecurityGroups'] is not None:
                for security_group in cluster['SecurityGroups']:
                    key = self.to_safe("security_group_" + security_group['SecurityGroupId'])
                    self.push(self.inventory, key, dest)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)
 
        # Inventory: Group by engine
        if self.group_by_elasticache_engine and not is_redis:
            self.push(self.inventory, self.to_safe("elasticache_" + cluster['Engine']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', self.to_safe(cluster['Engine']))
 
        # Inventory: Group by parameter group
        if self.group_by_elasticache_parameter_group:
            self.push(self.inventory, self.to_safe("elasticache_parameter_group_" + cluster['CacheParameterGroup']['CacheParameterGroupName']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_parameter_groups', self.to_safe(cluster['CacheParameterGroup']['CacheParameterGroupName']))
 
        # Inventory: Group by replication group
        if self.group_by_elasticache_replication_group and 'ReplicationGroupId' in cluster and cluster['ReplicationGroupId']:
            self.push(self.inventory, self.to_safe("elasticache_replication_group_" + cluster['ReplicationGroupId']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_replication_groups', self.to_safe(cluster['ReplicationGroupId']))
 
        # Global Tag: all ElastiCache clusters
        self.push(self.inventory, 'elasticache_clusters', cluster['CacheClusterId'])
 
        host_info = self.get_host_info_dict_from_describe_dict(cluster)
 
        self.inventory["_meta"]["hostvars"][dest] = host_info
 
        # Add the nodes
        for node in cluster['CacheNodes']:
            self.add_elasticache_node(node, cluster, region)
 
    def add_elasticache_node(self, node, cluster, region):
        ''' Adds an ElastiCache node to the inventory and index, as long as
        it is addressable '''
 
        # Only want available nodes unless all_elasticache_nodes is True
        if not self.all_elasticache_nodes and node['CacheNodeStatus'] != 'available':
            return
 
        # Select the best destination address
        dest = node['Endpoint']['Address']
 
        if not dest:
            # Skip nodes we cannot address (e.g. private VPC subnet)
            return
 
        node_id = self.to_safe(cluster['CacheClusterId'] + '_' + node['CacheNodeId'])
 
        # Add to index
        self.index[dest] = [region, node_id]
 
        # Inventory: Group by node ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[node_id] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', node_id)
 
        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)
 
        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, cluster['PreferredAvailabilityZone'], dest)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, cluster['PreferredAvailabilityZone'])
                self.push_group(self.inventory, 'zones', cluster['PreferredAvailabilityZone'])
 
        # Inventory: Group by node type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + cluster['CacheNodeType'])
            self.push(self.inventory, type_name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)
 
        # Inventory: Group by VPC (information not available in the current
        # AWS API version for ElastiCache)
 
        # Inventory: Group by security group
        if self.group_by_security_group:
 
            # Check for the existence of the 'SecurityGroups' key and also if
            # this key has some value. When the cluster is not placed in a SG
            # the query can return None here and cause an error.
            if 'SecurityGroups' in cluster and cluster['SecurityGroups'] is not None:
                for security_group in cluster['SecurityGroups']:
                    key = self.to_safe("security_group_" + security_group['SecurityGroupId'])
                    self.push(self.inventory, key, dest)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)
 
        # Inventory: Group by engine
        if self.group_by_elasticache_engine:
            self.push(self.inventory, self.to_safe("elasticache_" + cluster['Engine']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', self.to_safe("elasticache_" + cluster['Engine']))
 
        # Inventory: Group by parameter group (done at cluster level)
 
        # Inventory: Group by replication group (done at cluster level)
 
        # Inventory: Group by ElastiCache Cluster
        if self.group_by_elasticache_cluster:
            self.push(self.inventory, self.to_safe("elasticache_cluster_" + cluster['CacheClusterId']), dest)
 
        # Global Tag: all ElastiCache nodes
        self.push(self.inventory, 'elasticache_nodes', dest)
 
        host_info = self.get_host_info_dict_from_describe_dict(node)
 
        if dest in self.inventory["_meta"]["hostvars"]:
            self.inventory["_meta"]["hostvars"][dest].update(host_info)
        else:
            self.inventory["_meta"]["hostvars"][dest] = host_info
 
    def add_elasticache_replication_group(self, replication_group, region):
        ''' Adds an ElastiCache replication group to the inventory and index '''
 
        # Only want available clusters unless all_elasticache_replication_groups is True
        if not self.all_elasticache_replication_groups and replication_group['Status'] != 'available':
            return
 
        # Skip clusters we cannot address (e.g. private VPC subnet or clustered redis)
        if replication_group['NodeGroups'][0]['PrimaryEndpoint'] is None or \
           replication_group['NodeGroups'][0]['PrimaryEndpoint']['Address'] is None:
            return
 
        # Select the best destination address (PrimaryEndpoint)
        dest = replication_group['NodeGroups'][0]['PrimaryEndpoint']['Address']
 
        # Add to index
        self.index[dest] = [region, replication_group['ReplicationGroupId']]
 
        # Inventory: Group by ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[replication_group['ReplicationGroupId']] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', replication_group['ReplicationGroupId'])
 
        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)
 
        # Inventory: Group by availability zone (doesn't apply to replication groups)
 
        # Inventory: Group by node type (doesn't apply to replication groups)
 
        # Inventory: Group by VPC (information not available in the current
        # AWS API version for replication groups
 
        # Inventory: Group by security group (doesn't apply to replication groups)
        # Check this value in cluster level
 
        # Inventory: Group by engine (replication groups are always Redis)
        if self.group_by_elasticache_engine:
            self.push(self.inventory, 'elasticache_redis', dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', 'redis')
 
        # Global Tag: all ElastiCache clusters
        self.push(self.inventory, 'elasticache_replication_groups', replication_group['ReplicationGroupId'])
 
        host_info = self.get_host_info_dict_from_describe_dict(replication_group)
 
        self.inventory["_meta"]["hostvars"][dest] = host_info
 
    def get_route53_records(self):
        ''' Get and store the map of resource records to domain names that
        point to them. '''
 
        if self.boto_profile:
            r53_conn = route53.Route53Connection(profile_name=self.boto_profile)
        else:
            r53_conn = route53.Route53Connection()
        all_zones = r53_conn.get_zones()
 
        route53_zones = [zone for zone in all_zones if zone.name[:-1] not in self.route53_excluded_zones]
 
        self.route53_records = {}
 
        for zone in route53_zones:
            rrsets = r53_conn.get_all_rrsets(zone.id)
 
            for record_set in rrsets:
                record_name = record_set.name
 
                if record_name.endswith('.'):
                    record_name = record_name[:-1]
 
                for resource in record_set.resource_records:
                    self.route53_records.setdefault(resource, set())
                    self.route53_records[resource].add(record_name)
 
    def get_instance_route53_names(self, instance):
        ''' Check if an instance is referenced in the records we have from
        Route53. If it is, return the list of domain names pointing to said
        instance. If nothing points to it, return an empty list. '''
 
        instance_attributes = ['public_dns_name', 'private_dns_name',
                               'ip_address', 'private_ip_address']
 
        name_list = set()
 
        for attrib in instance_attributes:
            try:
                value = getattr(instance, attrib)
            except AttributeError:
                continue
 
            if value in self.route53_records:
                name_list.update(self.route53_records[value])
 
        return list(name_list)
 
    def get_host_info_dict_from_instance(self, instance):
        instance_vars = {}
        for key in vars(instance):
            value = getattr(instance, key)
            key = self.to_safe('ec2_' + key)
 
            # Handle complex types
            # state/previous_state changed to properties in boto in https://github.com/boto/boto/commit/a23c379837f698212252720d2af8dec0325c9518
            if key == 'ec2__state':
                instance_vars['ec2_state'] = instance.state or ''
                instance_vars['ec2_state_code'] = instance.state_code
            elif key == 'ec2__previous_state':
                instance_vars['ec2_previous_state'] = instance.previous_state or ''
                instance_vars['ec2_previous_state_code'] = instance.previous_state_code
            elif isinstance(value, (int, bool)):
                instance_vars[key] = value
            elif isinstance(value, six.string_types):
                instance_vars[key] = value.strip()
            elif value is None:
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2__placement':
                instance_vars['ec2_placement'] = value.zone
            elif key == 'ec2_tags':
                for k, v in value.items():
                    if self.expand_csv_tags and ',' in v:
                        v = list(map(lambda x: x.strip(), v.split(',')))
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join([str(i) for i in group_ids])
                instance_vars["ec2_security_group_names"] = ','.join([str(i) for i in group_names])
            elif key == 'ec2_block_device_mapping':
                instance_vars["ec2_block_devices"] = {}
                for k, v in value.items():
                    instance_vars["ec2_block_devices"][os.path.basename(k)] = v.volume_id
            else:
                pass
                # TODO Product codes if someone finds them useful
                # print key
                # print type(value)
                # print value
 
        instance_vars[self.to_safe('ec2_account_id')] = self.aws_account_id
 
        return instance_vars
 
    def get_host_info_dict_from_describe_dict(self, describe_dict):
        ''' Parses the dictionary returned by the API call into a flat list
            of parameters. This method should be used only when 'describe' is
            used directly because Boto doesn't provide specific classes. '''
 
        # I really don't agree with prefixing everything with 'ec2'
        # because EC2, RDS and ElastiCache are different services.
        # I'm just following the pattern used until now to not break any
        # compatibility.
 
        host_info = {}
        for key in describe_dict:
            value = describe_dict[key]
            key = self.to_safe('ec2_' + self.uncammelize(key))
 
            # Handle complex types
 
            # Target: Memcached Cache Clusters
            if key == 'ec2_configuration_endpoint' and value:
                host_info['ec2_configuration_endpoint_address'] = value['Address']
                host_info['ec2_configuration_endpoint_port'] = value['Port']
 
            # Target: Cache Nodes and Redis Cache Clusters (single node)
            if key == 'ec2_endpoint' and value:
                host_info['ec2_endpoint_address'] = value['Address']
                host_info['ec2_endpoint_port'] = value['Port']
 
            # Target: Redis Replication Groups
            if key == 'ec2_node_groups' and value:
                host_info['ec2_endpoint_address'] = value[0]['PrimaryEndpoint']['Address']
                host_info['ec2_endpoint_port'] = value[0]['PrimaryEndpoint']['Port']
                replica_count = 0
                for node in value[0]['NodeGroupMembers']:
                    if node['CurrentRole'] == 'primary':
                        host_info['ec2_primary_cluster_address'] = node['ReadEndpoint']['Address']
                        host_info['ec2_primary_cluster_port'] = node['ReadEndpoint']['Port']
                        host_info['ec2_primary_cluster_id'] = node['CacheClusterId']
                    elif node['CurrentRole'] == 'replica':
                        host_info['ec2_replica_cluster_address_' + str(replica_count)] = node['ReadEndpoint']['Address']
                        host_info['ec2_replica_cluster_port_' + str(replica_count)] = node['ReadEndpoint']['Port']
                        host_info['ec2_replica_cluster_id_' + str(replica_count)] = node['CacheClusterId']
                        replica_count += 1
 
            # Target: Redis Replication Groups
            if key == 'ec2_member_clusters' and value:
                host_info['ec2_member_clusters'] = ','.join([str(i) for i in value])
 
            # Target: All Cache Clusters
            elif key == 'ec2_cache_parameter_group':
                host_info["ec2_cache_node_ids_to_reboot"] = ','.join([str(i) for i in value['CacheNodeIdsToReboot']])
                host_info['ec2_cache_parameter_group_name'] = value['CacheParameterGroupName']
                host_info['ec2_cache_parameter_apply_status'] = value['ParameterApplyStatus']
 
            # Target: Almost everything
            elif key == 'ec2_security_groups':
 
                # Skip if SecurityGroups is None
                # (it is possible to have the key defined but no value in it).
                if value is not None:
                    sg_ids = []
                    for sg in value:
                        sg_ids.append(sg['SecurityGroupId'])
                    host_info["ec2_security_group_ids"] = ','.join([str(i) for i in sg_ids])
 
            # Target: Everything
            # Preserve booleans and integers
            elif isinstance(value, (int, bool)):
                host_info[key] = value
 
            # Target: Everything
            # Sanitize string values
            elif isinstance(value, six.string_types):
                host_info[key] = value.strip()
 
            # Target: Everything
            # Replace None by an empty string
            elif value is None:
                host_info[key] = ''
 
            else:
                # Remove non-processed complex types
                pass
 
        return host_info
 
    def get_host_info(self):
        ''' Get variables about a specific host '''
 
        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()
 
        if self.args.host not in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if self.args.host not in self.index:
                # host might not exist anymore
                return self.json_format_dict({}, True)
 
        (region, instance_id) = self.index[self.args.host]
 
        instance = self.get_instance(region, instance_id)
        return self.json_format_dict(self.get_host_info_dict_from_instance(instance), True)
 
    def push(self, my_dict, key, element):
        ''' Push an element onto an array that may not have been defined in
        the dict '''
        group_info = my_dict.setdefault(key, [])
        if isinstance(group_info, dict):
            host_list = group_info.setdefault('hosts', [])
            host_list.append(element)
        else:
            group_info.append(element)
 
    def push_group(self, my_dict, key, element):
        ''' Push a group as a child of another group. '''
        parent_group = my_dict.setdefault(key, {})
        if not isinstance(parent_group, dict):
            parent_group = my_dict[key] = {'hosts': parent_group}
        child_groups = parent_group.setdefault('children', [])
        if element not in child_groups:
            child_groups.append(element)
 
    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''
 
        with open(self.cache_path_cache, 'r') as f:
            json_inventory = f.read()
            return json_inventory
 
    def load_index_from_cache(self):
        ''' Reads the index from the cache file sets self.index '''
 
        with open(self.cache_path_index, 'rb') as f:
            self.index = json.load(f)
 
    def write_to_cache(self, data, filename):
        ''' Writes data in JSON format to a file '''
 
        json_data = self.json_format_dict(data, True)
        with open(filename, 'w') as f:
            f.write(json_data)
 
    def uncammelize(self, key):
        temp = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', temp).lower()
 
    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = r"[^A-Za-z0-9\_"
        if not self.replace_dash_in_groups:
            regex += r"\-"
        return re.sub(regex + "]", "_", word)
 
    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''
 
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2, default=self._json_serial)
        else:
            return json.dumps(data, default=self._json_serial)
 
 
if __name__ == '__main__':
    # Run the script
    Ec2Inventory()