import re
with open('app.py', 'r') as f:
    content = f.read()
# regions 엔드포인트를 실제 AWS API 호출로 수정
new_regions_code = '''
@app.route('/api/regions')
def get_regions():
    try:
        import boto3
        ec2 = boto3.client('ec2', region_name='us-west-2')
        response = ec2.describe_regions()
        regions = [region['RegionName'] for region in response['Regions']]
        return jsonify({'regions': regions})
    except Exception as e:
        print(f'AWS API Error: {e}')
        return jsonify({'regions': ['us-west-2', 'us-east-1']})  # fallback
'''
# 기존 regions 엔드포인트 찾기 및 교체
pattern = r'@app\.route\(\'/api/regions\'\)[\s\S]*?return jsonify\(\{"regions": \[\]\}\)'
if re.search(pattern, content):
    content = re.sub(pattern, new_regions_code.strip(), content)
    with open('app.py', 'w') as f:
        f.write(content)
    print('regions API updated successfully')
else:
    print('regions API pattern not found')
