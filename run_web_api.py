# from flask import Flask, request, jsonify
# import pythoncom
# from win32com.client import Dispatch
#
# app = Flask(__name__)
#
# def get_dcom_object():
#     pythoncom.CoInitialize()
#     return Dispatch("Python.RequestProcessor")
#
# @app.route('/receive', methods=['POST'])
# def receive_request():
#     data = request.json.get('data')
#     return jsonify({'message': f'Yêu cầu đã được tiếp nhận: {data}'})
#
# @app.route('/analyze', methods=['POST'])
# def analyze_request():
#     data = request.json.get('data')
#     processor = get_dcom_object()
#     result = processor.analyze_request(data)
#     return jsonify({'result': result})
#
# @app.route('/process', methods=['POST'])
# def process_request():
#     data = request.json.get('data')
#     processor = get_dcom_object()
#     result = processor.process_request(data)
#     return jsonify({'result': result})
#
# @app.route('/track', methods=['GET'])
# def track_request():
#     # Giả lập theo dõi yêu cầu
#     return jsonify({'status': 'Yêu cầu đang được xử lý'})
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
#
#

from web_api.api import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

