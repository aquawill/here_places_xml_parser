import csv
import json
import os

import xmltodict

# root = 'C:\\Users\\guanlwu\\Desktop\\TWN'
quality_level_requirement = []
root = input('Root of Places XML files: ')
if os.path.exists(root):
    quality_level_input = input('Required quality levels (12345): ')
    if len(quality_level_input) > 0:
        for digit in quality_level_input:
            if int(digit) in [1, 2, 3, 4, 5]:
                quality_level_requirement.append(int(digit))
    else:
        quality_level_requirement = [1, 2, 3, 4, 5]

with open(os.path.join(root, 'merged.csv'), mode='w', encoding='utf-8', newline='') as csv_output:
    fieldnames = ['FileName', 'PlaceId', 'QualityLevel', 'PrimaryName', 'CategoryId', 'CategoryName', 'AddressLabel', 'ChainId', 'ChainNameEng', 'RoutingLocationLat', 'RoutingLocationLng', 'DisplayLocationLat', 'DisplayLocationLng']
    writer = csv.writer(csv_output, delimiter='\t')
    writer.writerow(fieldnames)
    for rootDir, dirs, files in os.walk(root):
        for file in files:
            file_name, file_extension = os.path.splitext(file)
            if file_extension.lower() == '.xml':
                print(file)
                with open(os.path.join(rootDir, file), mode='r', encoding='utf-8') as fd:
                    inputDict = dict(xmltodict.parse(fd.read()))
                    outputDict = json.loads(json.dumps(inputDict))
                    placeList = outputDict['PlaceList']['Place']
                    for place in placeList:
                        Location = place['LocationList']['Location']
                        try:
                            identity = place['Identity']
                            placeId = identity.get('PlaceId')
                            qualityLevel = int(identity.get('QualityLevel'))
                            if qualityLevel in quality_level_requirement:
                                locationId = Location.get('@locationId')
                                label = Location.get('@label')
                                address = Location.get('Address')
                                geoPositionList = Location.get('GeoPositionList').get('GeoPosition')
                                geoPositionRouting = {'lat': None, 'lng': None}
                                geoPositionDisplay = {'lat': None, 'lng': None}
                                if isinstance(geoPositionList, list):
                                    for geoPosition in geoPositionList:
                                        if geoPosition.get("@type") == 'ROUTING':
                                            geoPositionRouting['lat'] = geoPosition.get('Latitude')
                                            geoPositionRouting['lng'] = geoPosition.get('Longitude')
                                        if geoPosition.get("@type") == 'DISPLAY':
                                            geoPositionDisplay['lat'] = geoPosition.get('Latitude')
                                            geoPositionDisplay['lng'] = geoPosition.get('Longitude')
                                elif isinstance(geoPositionList, dict):
                                    geoPosition = geoPositionList
                                    if geoPosition.get("@type") == 'ROUTING':
                                        geoPositionRouting['lat'] = geoPosition.get('Latitude')
                                        geoPositionRouting['lng'] = geoPosition.get('Longitude')
                                    if geoPosition.get("@type") == 'DISPLAY':
                                        geoPositionDisplay['lat'] = geoPosition.get('Latitude')
                                        geoPositionDisplay['lng'] = geoPosition.get('Longitude')

                                content = place.get('Content')
                                content_base = content.get('Base')

                                # parse name
                                content_base_nameList = content_base.get('NameList')
                                content_base_nameList_name = content_base_nameList.get('Name')
                                primary_name = ''
                                primary_name_located = False
                                if isinstance(content_base_nameList_name, list):
                                    for name_element in content_base_nameList_name:
                                        if name_element.get('@primaryFlag') == 'true':
                                            primary_name = name_element
                                            primary_name_located = True
                                    if not primary_name_located:
                                        primary_name = content_base_nameList_name[0]
                                else:
                                    primary_name = content_base_nameList_name
                                    primary_name_located = True
                                primary_name_textList = primary_name.get('TextList')
                                primary_name_textList_text = primary_name_textList.get('Text')
                                primary_name_text = ''
                                if isinstance(primary_name_textList_text, list):
                                    for primary_name_text_element in primary_name_textList_text:
                                        baseText = primary_name_text_element.get('BaseText')
                                        if baseText.get('@languageType') == '':
                                            primary_name_text = baseText.get('#text')
                                            # primary_name_string_located = True
                                            break
                                else:
                                    baseText = primary_name_textList_text.get('BaseText')
                                    if baseText.get('@languageType') == '':
                                        primary_name_text = baseText.get('#text')
                                if primary_name_text == '':
                                    primary_name_text = primary_name_textList_text.get('BaseText').get('#text')

                                # parse category
                                content_base_categoryList = content_base.get('CategoryList')
                                content_base_categoryList_category = content_base_categoryList.get('Category')
                                primary_category = ''
                                if isinstance(content_base_categoryList_category, list):
                                    for category_element in content_base_categoryList_category:
                                        if category_element.get('@categorySystem') == 'navteq-lcms' and category_element.get('@primaryFlag') == 'true':
                                            primary_category = category_element
                                            break
                                        elif category_element.get('@categorySystem') == 'navteq-lcms' and category_element.get('@primaryFlag') == 'false':
                                            primary_category = category_element
                                            break
                                else:
                                    primary_category = content_base_categoryList_category
                                primary_category_categoryId = primary_category.get('CategoryId')
                                primary_category_categoryName = primary_category.get('CategoryName')
                                primary_category_categoryName_text = primary_category_categoryName.get('Text')
                                primary_category_categoryName_text_text = primary_category_categoryName_text.get('#text')
                                primary_category_description = primary_category.get('Description')
                                primary_category_description_text = primary_category_description.get('Text')
                                primary_category_description_text_text = primary_category_description_text.get('#text')

                                # parse chains
                                chain_id = ''
                                chain_name_text = ''
                                if content_base.get('ChainList'):
                                    chainList = content_base.get('ChainList')
                                    # print(chainList.get('Chain'))
                                    chain_id = chainList.get('Chain').get('Id')
                                    chain_name = chainList.get('Chain').get('Name').get('Text')
                                    if chain_name.get('@type') == 'OFFICIAL':
                                        chain_name_text = chain_name.get('#text')
                                    # print(chain_id, chain_name_text)
                                line = [file, placeId, qualityLevel, primary_name_text, primary_category_categoryId, primary_category_categoryName_text_text, label, chain_id, chain_name_text, geoPositionRouting.get('lat'), geoPositionRouting.get('lng'), geoPositionDisplay.get('lat'), geoPositionDisplay.get('lng')]
                                writer.writerow(line)
                        except Exception as e:
                            print(place)
                            print(e.with_traceback())
