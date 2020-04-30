import http.server
import socketserver

# OK, so this is accessible, and returns the default index.html
# at 192.168.1.95:8000 for me. The question now is how to build
# the html. I think I could just put a simple template in 
# the sensor.py file or here, then output index.html from it, along
# with an image from matplotlib (or base64 encoded inline).
# Then just serve index.html showing tail 1440min/config.freq, 1000, 
# tail 10000, or whatever max points you want.

# Or just return an html file from a template inlined here
# that loads the images and a tail of the logs and results.csv

# Then also serve the csv, log files, and inline basics?


PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Serving at port: ", PORT)
    httpd.serve_forever()