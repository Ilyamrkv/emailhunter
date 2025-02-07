import logging
from flask import Flask, render_template, request, Response, jsonify, send_file
from email_parser import EmailParser
import json
import csv
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "email_parser_secret_key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST', 'GET'])
def parse_domains():
    try:
        if request.method == 'GET':
            # For SSE connection
            return Response(
                "data: connected\n\n",
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
            )

        data = request.get_json()
        domains = data.get('domains', '').split('\n')
        domains = [domain.strip() for domain in domains if domain.strip()]

        if not domains:
            return jsonify({'error': 'No valid domains provided'}), 400

        parser = EmailParser()
        def generate():
            for domain, emails in parser.parse_domains(domains):
                yield f"data: {json.dumps({'domain': domain, 'emails': list(emails)})}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        logger.error(f"Error during parsing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export_csv():
    try:
        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({'error': 'No data provided'}), 400

        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Domain', 'Email'])  # CSV header

        # Write data
        for item in data['results']:
            domain = item['domain']
            emails = item['emails']
            if isinstance(emails, list):
                for email in emails:
                    writer.writerow([domain, email])
            else:
                writer.writerow([domain, emails])  # In case of error message

        # Prepare response
        output = si.getvalue()
        si.close()

        return Response(
            output,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=email_results.csv',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )

    except Exception as e:
        logger.error(f"Error during CSV export: {str(e)}")
        return jsonify({'error': str(e)}), 500