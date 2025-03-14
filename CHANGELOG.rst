===============
Version History
===============

v7.2.3
------

* Bump django from 5.0.11 to 5.0.13 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/312>`_
* Bump jinja2 from 3.1.5 to 3.1.6 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/310>`_
* Updates for the ASummary State view on Summit. `<https://github.com/lsst-ts/LOVE-manager/pull/309>`_
* Bump django from 5.0.9 to 5.0.11 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/308>`_
* Bump twisted from 23.10.0 to 24.7.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/307>`_
* Bump jinja2 from 3.1.4 to 3.1.5 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/306>`_
* Bump cryptography from 42.0.4 to 44.0.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/305>`_
* Bump django from 5.0.8 to 5.0.9 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/285>`_

v7.2.2
------

* Replace EPM:1 CSC per ESS:303 in the SummaryState view on BTS. `<https://github.com/lsst-ts/LOVE-manager/pull/304>`_
* Add Simonyi Monitor view to ui-framework summit fixtures. `<https://github.com/lsst-ts/LOVE-manager/pull/303>`_

v7.2.1
------

* Add MTM1M3TS and MTVMS:0 to SummaryState view on BTS and TTS. `<https://github.com/lsst-ts/LOVE-manager/pull/302>`_
* Add details about Channels Layer configurations to README. `<https://github.com/lsst-ts/LOVE-manager/pull/298>`_
* Remove labels param from payload on jira_ticket method. `<https://github.com/lsst-ts/LOVE-manager/pull/301>`_

v7.2.0
------

* Refactor jira_ticket method to comply with new OBS systems hierarchy. `<https://github.com/lsst-ts/LOVE-manager/pull/300>`_

v7.1.7
------

* Convert narrativelog date_begin and date_end UTC datetimes to TAI. `<https://github.com/lsst-ts/LOVE-manager/pull/299>`_
* Add recently added CSCs to SummaryState view on BTS. `<https://github.com/lsst-ts/LOVE-manager/pull/297>`_
* Make channels layer group expiry parameter configurable through an environment variable. `<https://github.com/lsst-ts/LOVE-manager/pull/296>`_

v7.1.6
------

* Add EAS:0 CSC to summit ASummary State view on Summit. `<https://github.com/lsst-ts/LOVE-manager/pull/295>`_
* Show error details from queries to the JIRA REST API. `<https://github.com/lsst-ts/LOVE-manager/pull/294>`_
* Make the SummaryState view as the official one for TTS and BTS. `<https://github.com/lsst-ts/LOVE-manager/pull/293>`_
* Refactor get_jira_obs_report method to account for JIRA REST API user timezone. `<https://github.com/lsst-ts/LOVE-manager/pull/292>`_

v7.1.5
------

* Add LedProjector and LinearStage CSCs to ASummaryState view fixture on Summit. `<https://github.com/lsst-ts/LOVE-manager/pull/291>`_

v7.1.4
------

* Add MTM1M3TS to ASummaryState view fixture on Summit. `<https://github.com/lsst-ts/LOVE-manager/pull/289>`_
* Standardize SummaryState view on TTS and BTS. `<https://github.com/lsst-ts/LOVE-manager/pull/288>`_

v7.1.3
------

* Add ESS earthquake sensor CSC index for summit. `<https://github.com/lsst-ts/LOVE-manager/pull/287>`_

v7.1.2
------

* Fix date conversion for the get_jira_obs_report method `<https://github.com/lsst-ts/LOVE-manager/pull/284>`_
* Make sure that all ESS CSC indices are up to date in the base, tucson and summit initial datasets. `<https://github.com/lsst-ts/LOVE-manager/pull/286>`_

v7.1.1
------

* Fix issue with django admin panel not accessible `<https://github.com/lsst-ts/LOVE-manager/pull/283>`_
* Add ESS:109 to the summit initial dataset. `<https://github.com/lsst-ts/LOVE-manager/pull/281>`_
* Fix issue with update_time_lost being called on jira tickets that doesn't have a time lost defined `<https://github.com/lsst-ts/LOVE-manager/pull/282>`_

v7.1.0
------

* Add identity to issued commands through the commander view `<https://github.com/lsst-ts/LOVE-manager/pull/278>`_
* Remove cmd user creation for production deployments `<https://github.com/lsst-ts/LOVE-manager/pull/280>`_

v7.0.3
------

* Fix issue with update_time_lost method `<https://github.com/lsst-ts/LOVE-manager/pull/277>`_

v7.0.2
------

* Add accumulation of time lost in Jira comments `<https://github.com/lsst-ts/LOVE-manager/pull/275>`_

v7.0.1
------

* Adjust websockets routing as prefix is not needed anymore `<https://github.com/lsst-ts/LOVE-manager/pull/276>`_

v7.0.0
------

* Remove deprecated deployment stages from the Jenkinsfile `<https://github.com/lsst-ts/LOVE-manager/pull/274>`_
* Bump requests from 2.31.0 to 2.32.2 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/273>`_
* Bump django from 5.0.7 to 5.0.8 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/272>`_
* Bump zipp from 3.1.0 to 3.19.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/264>`_
* Bump certifi from 2023.7.22 to 2024.7.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/263>`_
* Bump urllib3 from 1.26.18 to 1.26.19 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/256>`_
* Bump jinja2 from 2.11.3 to 3.1.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/249>`_
* Bump MarkupSafe from 1.1.1 to 2.1.5 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/271>`_
* Bump sqlparse from 0.4.4 to 0.5.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/247>`_
* Bump idna from 2.9 to 3.7 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/246>`_
* Bump pillow from 10.0.1 to 10.3.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/244>`_
* Update core dependencies and remove final traces of the Authlist feature `<https://github.com/lsst-ts/LOVE-manager/pull/270>`_

v6.0.8
------

* Add more CSCs to summit summary state view `<https://github.com/lsst-ts/LOVE-manager/pull/255>`_

v6.0.7
------

* Remove unused ui_framework fixture views `<https://github.com/lsst-ts/LOVE-manager/pull/269>`_
* Remove conditional on authentication views that prevented commanding permissions to be overwritten `<https://github.com/lsst-ts/LOVE-manager/pull/268>`_

v6.0.6
------

* Add CBP:0 to Summit ASummary State View `<https://github.com/lsst-ts/LOVE-manager/pull/267>`_
* Add Electrometer:101 and Electrometer:102 to Summit ASummary State View `<https://github.com/lsst-ts/LOVE-manager/pull/266>`_

v6.0.5
------

* Strip white spaces from human written fields in the ole_send_night_report function `<https://github.com/lsst-ts/LOVE-manager/pull/265>`_

v6.0.4
------

* Remove time loss calculation from nightreport mailing `<https://github.com/lsst-ts/LOVE-manager/pull/262>`_
* Remove unused dependencies `<https://github.com/lsst-ts/LOVE-manager/pull/261>`_

v6.0.3
------

* Add EPM:1 to ASummary State View on BTS and EPM:301 to summit `<https://github.com/lsst-ts/LOVE-manager/pull/260>`_

v6.0.2
------

* Add OCPS:101 to ASummary State View on Summit `<https://github.com/lsst-ts/LOVE-manager/pull/258>`_
* Bump django from 3.1.14 to 3.2.25 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/257>`_

v6.0.1
------

* Improve LOVE night report email plain text format `<https://github.com/lsst-ts/LOVE-manager/pull/254>`_

v6.0.0
------

* Remove Authorize CSC components and references `<https://github.com/lsst-ts/LOVE-manager/pull/253>`_

v5.19.3
-------

* Add ESS:107 and ESS:108 to BTS and Summit summary state view fixtures `<https://github.com/lsst-ts/LOVE-manager/pull/251>`_

v5.19.2
-------

* Fix API fixture to point to correct default LOVE configuration file `<https://github.com/lsst-ts/LOVE-manager/pull/250>`_

v5.19.1
-------

* Bump cryptography from 41.0.6 to 42.0.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/238>`_
* Add TunableLaser to summit summary state view `<https://github.com/lsst-ts/LOVE-manager/pull/248>`_

v5.19.0
-------

* Add mailing feature so it can be used by the Night Report `<https://github.com/lsst-ts/LOVE-manager/pull/245>`_

v5.18.1
-------

* Add ScriptQueue:3 and Scheduler:3 to ASummary State View on Summit `<https://github.com/lsst-ts/LOVE-manager/pull/243>`_

v5.18.0
-------

* Add Night Report implementation `<https://github.com/lsst-ts/LOVE-manager/pull/242>`_

v5.17.4
-------

* Update OBS jira project id and roll back way of setting it `<https://github.com/lsst-ts/LOVE-manager/pull/240>`_

v5.17.3
-------

* Adjustments for new JIRA Cloud REST API interface `<https://github.com/lsst-ts/LOVE-manager/pull/239>`_

v5.17.2
-------

* Update summary state fixture views with a new ESS CSC `<https://github.com/lsst-ts/LOVE-manager/pull/237>`_

v5.17.1
-------

* Extend OLE update methods to allow JIRA ticket attachment `<https://github.com/lsst-ts/LOVE-manager/pull/235>`_

v5.17.0
-------

* Add M1M3 bump tests reports endpoint `<https://github.com/lsst-ts/LOVE-manager/pull/232>`_

v5.16.1
-------

* Remove unused urls and templates `<https://github.com/lsst-ts/LOVE-manager/pull/229>`_

v5.16.0
-------

* Add new `redirect` app to provide a url shortener feature `<https://github.com/lsst-ts/LOVE-manager/pull/228>`_

v5.15.1
-------

* Increase users uploads max file size `<https://github.com/lsst-ts/LOVE-manager/pull/227>`_
* Bump cryptography from 41.0.4 to 41.0.6 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/226>`_
* Add missing base fixtures `<https://github.com/lsst-ts/LOVE-manager/pull/225>`_

v5.15.0
-------

* Manager performance improvements `<https://github.com/lsst-ts/LOVE-manager/pull/224>`_
* Bump twisted from 22.10.0 to 23.10.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/222>`_

v5.14.10
--------

* Update WeatherStation component salindex on UI Framework fixtures `<https://github.com/lsst-ts/LOVE-manager/pull/223>`_

v5.14.9
-------

* Remove JIRA fields ids mapping `<https://github.com/lsst-ts/LOVE-manager/pull/221>`_
* Bump urllib3 from 1.26.17 to 1.26.18 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/218>`_

v5.14.8
-------

* Reduce miliseconds part of time of incident timestamps `<https://github.com/lsst-ts/LOVE-manager/pull/217>`_
* Possibly malformed YAML in script dialog causes crash loop on subsequent use `<https://github.com/lsst-ts/LOVE-manager/pull/216>`_

v5.14.7
-------

* Hotfix to update docs reference `<https://github.com/lsst-ts/LOVE-manager/pull/215>`_
* Move docs creation to CI `<https://github.com/lsst-ts/LOVE-manager/pull/211>`_
* Add ts_pre_commit_conf `<https://github.com/lsst-ts/LOVE-manager/pull/213>`_
* Bump pillow from 9.3.0 to 10.0.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/214>`_
* Bump urllib3 from 1.26.5 to 1.26.17 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/212>`_
* Bump cryptography from 41.0.3 to 41.0.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/205>`_

v5.14.6
-------

* Hotfix runserver.sh `<https://github.com/lsst-ts/LOVE-manager/pull/210>`_

v5.14.5
-------

* Update COPYRIGHT.md `<https://github.com/lsst-ts/LOVE-manager/pull/209>`_
* Improve copyright file `<https://github.com/lsst-ts/LOVE-manager/pull/208>`_
* Hotfix/v5.14.5 `<https://github.com/lsst-ts/LOVE-manager/pull/207>`_
* LOVE License `<https://github.com/lsst-ts/LOVE-manager/pull/206>`_

v5.14.4
-------

* Adjust jira ticket creation payload for custom fields `<https://github.com/lsst-ts/LOVE-manager/pull/204>`_

v5.14.3
-------

* Extend OLE narrativelog view to implement new jira fields `<https://github.com/lsst-ts/LOVE-manager/pull/201>`_

v5.14.2
--------

* Extend OLE views to allow multiple file upload `<https://github.com/lsst-ts/LOVE-manager/pull/203>`_
* Add string representation for ScriptConfiguration model `<https://github.com/lsst-ts/LOVE-manager/pull/202>`_

v5.14.1
--------

* Add view updates for summit, TTS and BTS `<https://github.com/lsst-ts/LOVE-manager/pull/200>`_
* Bump cryptography from 41.0.2 to 41.0.3 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/199>`_
* Bump certifi from 2022.12.7 to 2023.7.22 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/198>`_
* Bump pygments from 2.7.4 to 2.15.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/197>`_
* Bump cryptography from 41.0.0 to 41.0.2 `<https://github.com/lsst-ts/LOVE-manager/pull/195>`_

v5.14.0
--------

* Extend LOVE manager routing system for subpath app serving `<https://github.com/lsst-ts/LOVE-manager/pull/196>`_

v5.13.0
--------

* Implement Control Location IP permissions `<https://github.com/lsst-ts/LOVE-manager/pull/194>`_
* LOVE screen sizes enhancement `<https://github.com/lsst-ts/LOVE-manager/pull/188>`_

v5.12.0
--------

* Add changelog checker github action `<https://github.com/lsst-ts/LOVE-manager/pull/193>`_
* Fix file handling on RemoteStorage class `<https://github.com/lsst-ts/LOVE-manager/pull/192>`_
* Hotfix/v5.11.0 `<https://github.com/lsst-ts/LOVE-manager/pull/191>`_
* Extend Manager to receive configuration for querying Commander `<https://github.com/lsst-ts/LOVE-manager/pull/189>`_
* Bump cryptography from 39.0.1 to 41.0.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/187>`_
* ScriptQueue Upgrade implementation `<https://github.com/lsst-ts/LOVE-manager/pull/186>`_

v5.11.2
--------

* Fix file handling on RemoteStorage class `<https://github.com/lsst-ts/LOVE-manager/pull/192>`_

v5.11.1
--------

* Hotfix/v5.11.0 `<https://github.com/lsst-ts/LOVE-manager/pull/191>`_
* Bump cryptography from 39.0.1 to 41.0.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/187>`_
* Bump requests from 2.23.0 to 2.31.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/185>`_

v5.11.0
--------

* Add remote storage method `<https://github.com/lsst-ts/LOVE-manager/pull/184>`_
* tickets/SITCOM-801 `<https://github.com/lsst-ts/LOVE-manager/pull/183>`_

v5.10.2
--------

* Bump sqlparse from 0.3.1 to 0.4.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/182>`_
* tickets/SITCOM-764  `<https://github.com/lsst-ts/LOVE-manager/pull/181>`_

v5.10.1
-------

* Add documentation for Control Location feature `<https://github.com/lsst-ts/LOVE-manager/pull/180>`_

v5.10.0
-------

* Add ControlLocation model `<https://github.com/lsst-ts/LOVE-manager/pull/179>`_

v5.9.2
-------

* Update docs: LOVE Config file `<https://github.com/lsst-ts/LOVE-manager/pull/178>`_
* Fix view header for LSSTCam `<https://github.com/lsst-ts/LOVE-manager/pull/177>`_
* Updates for summit and base `<https://github.com/lsst-ts/LOVE-manager/pull/176>`_

v5.9.1
-------

* Add repository version history `<https://github.com/lsst-ts/LOVE-manager/pull/175>`_
* Add GIS to summit ASummary State view. `<https://github.com/lsst-ts/LOVE-manager/pull/174>`_
* Remove encryption layer for channels-redis `<https://github.com/lsst-ts/LOVE-manager/pull/173>`_

v5.9.0
-------

* OLE implementation `<https://github.com/lsst-ts/LOVE-manager/pull/159>`_

v5.8.3
-------

* tickets/DM-36177 `<https://github.com/lsst-ts/LOVE-manager/pull/172>`_
* Add another CSC to ASummary State view. `<https://github.com/lsst-ts/LOVE-manager/pull/171>`_
* Bump cryptography from 3.3.2 to 39.0.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/170>`_
* tickets/SITCOM-630 `<https://github.com/lsst-ts/LOVE-manager/pull/169>`_
* Extend UI Framework permissions to normal users `<https://github.com/lsst-ts/LOVE-manager/pull/168>`_
* Remove py library as it is not used anymore after pytest upgrade `<https://github.com/lsst-ts/LOVE-manager/pull/167>`_
* Upgrade pytest dependencies `<https://github.com/lsst-ts/LOVE-manager/pull/166>`_
* Bump certifi from 2019.11.28 to 2022.12.7 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/165>`_


v5.8.2
-------

* Authlist extension `<https://github.com/lsst-ts/LOVE-manager/pull/164>`_

v5.8.1
------

* Bump pillow from 9.0.1 to 9.3.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/163>`_
* Extend and refactor LDAP login methods `<https://github.com/lsst-ts/LOVE-manager/pull/162>`_

v5.8.0
-------

* Bump twisted from 22.4.0 to 22.10.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/161>`_
* LDAP Implementation `<https://github.com/lsst-ts/LOVE-manager/pull/160>`_


v5.7.3
-------

* Add JSON file validation to ConfigFile admin form `<https://github.com/lsst-ts/LOVE-manager/pull/158>`_
* Refactor Authorize CSC connection `<https://github.com/lsst-ts/LOVE-manager/pull/157>`_
* Update dependencies `<https://github.com/lsst-ts/LOVE-manager/pull/156>`_

v5.7.1
-------

* Authlist adjustments `<https://github.com/lsst-ts/LOVE-manager/pull/154>`_

v5.7.0
-------

* Add ConfigFile selection storage `<https://github.com/lsst-ts/LOVE-manager/pull/153>`_
* Bump numpy from 1.21.0 to 1.22.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/152>`_

v5.6.0
-------

* Bump twisted from 22.2.0 to 22.4.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/151>`_
* Remove unnecessary print `<https://github.com/lsst-ts/LOVE-manager/pull/150>`_
* Update configuration file settings documentation `<https://github.com/lsst-ts/LOVE-manager/pull/149>`_
* tickets/SITCOM-277 `<https://github.com/lsst-ts/LOVE-manager/pull/148>`_
* Add EFD logMessage endpoint `<https://github.com/lsst-ts/LOVE-manager/pull/146>`_
* Add Observing Day time `<https://github.com/lsst-ts/LOVE-manager/pull/147>`_
* Update documentation to include info about LOVE Configuration File `<https://github.com/lsst-ts/LOVE-manager/pull/144>`_

v5.5.1
-------

* Upgrade to astropy 5.0.3 `<https://github.com/lsst-ts/LOVE-manager/pull/145>`_
* Bump pillow from 9.0.0 to 9.0.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/143>`_
* Bump twisted from 22.1.0 to 22.2.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/142>`_

v5.5.0
-------

* Refactor docker files path #141 `<https://github.com/lsst-ts/LOVE-manager/pull/141>`_
* Hotfix/update jenkinsfile #140 `<https://github.com/lsst-ts/LOVE-manager/pull/140>`_
* Bump twisted from 20.3.0 to 22.1.0 in /manager #139 `<https://github.com/lsst-ts/LOVE-manager/pull/139>`_
* Add Main TCS to views.py for the call to commander TCS and refactor of Test `<https://github.com/lsst-ts/LOVE-manager/pull/134>`

v5.4.0
-------

* Bump pillow from 8.3.2 to 9.0.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/138>`_
* Bump numpy from 1.18.1 to 1.21.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/137>`_
* Remove pillow in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/136>`_
* tickets/DM-31069 #135 `<https://github.com/lsst-ts/LOVE-manager/pull/135>`_
* Bump django from 3.1.13 to 3.1.14 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/133>`_
* Bump python-ldap from 3.2.0 to 3.4.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/132>`_
* Add endpoint to list EFD client instances `<https://github.com/lsst-ts/LOVE-manager/pull/131>`_

v5.3.0
-------

* Authlist implementation `<https://github.com/lsst-ts/LOVE-manager/pull/129>`_

v5.2.0
-------

* Allow manager to route traffic to different manager instances. `<https://github.com/lsst-ts/LOVE-manager/pull/130>`_
* Error when trying to delete a view that hasn't a thumbnail uploaded `<https://github.com/lsst-ts/LOVE-manager/pull/128>`_
* Bump babel from 2.8.0 to 2.9.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/127>`_
* Add configuration variables for channels-redis `<https://github.com/lsst-ts/LOVE-manager/pull/126>`_
* Bump django from 3.0.14 to 3.1.13 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/124>`_
* Bump pillow from 8.2.0 to 8.3.2 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/123>`_

v5.1.0
-------

* Remove deprecated heartbeat function `<https://github.com/lsst-ts/LOVE-manager/pull/122>`_
* Bump pillow from 8.1.1 to 8.2.0 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/119>`_

v5.0.1
-------

* Document LOVE-producer configuration `<https://github.com/lsst-ts/LOVE-manager/pull/121>`_
* Bump urllib3 from 1.25.8 to 1.26.5 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/117>`_


v5.0.0
-------

* Environment variable set for LOVE_CSC_PRODUCER `<https://github.com/lsst-ts/LOVE-manager/pull/115>`_
* Script logMessages is not compatible with the new Producer version #113 `<https://github.com/lsst-ts/LOVE-manager/pull/113>`_
* Add new Dockerfile for only serving static files `<https://github.com/lsst-ts/LOVE-manager/pull/112>`_
* Bump py from 1.8.1 to 1.10.0 in /manager #111 `<https://github.com/lsst-ts/LOVE-manager/pull/111>`_
* Bump autobahn from 20.3.1 to 20.12.3 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/110>`_
* Bump django from 3.0.12 to 3.0.14 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/109>`_
* Bump django from 3.0.7 to 3.0.12 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/107>`_
* Bump pygments from 2.6.1 to 2.7.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/106>`_
* Bump pyyaml from 5.3 to 5.4 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/105>`_
* Bump jinja2 from 2.11.1 to 2.11.3 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/104>`_
* Bump djangorestframework from 3.11.0 to 3.11.2 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/103>`_
* Bump pillow from 7.2.0 to 8.1.1 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/102>`_
* Support summit activities `<https://github.com/lsst-ts/LOVE-manager/pull/100>`_
* TCS API `<https://github.com/lsst-ts/LOVE-manager/pull/97>`_


v4.0.0
-------

* tickets/LOVE-29 `<https://github.com/lsst-ts/LOVE-manager/pull/98>`_
* Bump cryptography from 3.2 to 3.3.2 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/96>`_
* Include pre-commit config file `<https://github.com/lsst-ts/LOVE-manager/pull/95>`_
* Fix test_heartbeat.py `<https://github.com/lsst-ts/LOVE-manager/pull/94>`_
* Black formatter fixes `<https://github.com/lsst-ts/LOVE-manager/pull/93>`_
* Efd api `<https://github.com/lsst-ts/LOVE-manager/pull/92>`_
* Sonarqube fixes `<https://github.com/lsst-ts/LOVE-manager/pull/91>`_
* Emergency contacts `<https://github.com/lsst-ts/LOVE-manager/pull/90>`_
* Update jenkinsfile to publish documentation `<https://github.com/lsst-ts/LOVE-manager/pull/89>`_
* ConfigFile api `<https://github.com/lsst-ts/LOVE-manager/pull/88>`_
* Lovecsc http refactor `<https://github.com/lsst-ts/LOVE-manager/pull/87>`_
* Bump cryptography from 2.8 to 3.2 in /manager `<https://github.com/lsst-ts/LOVE-manager/pull/86>`_
