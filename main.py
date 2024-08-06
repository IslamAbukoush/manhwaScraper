import aiohttp
import asyncio
import os
import sys
import ssl
from bs4 import BeautifulSoup
from fpdf import FPDF
from aiohttp import TCPConnector

# Asynchronous function to download images
async def download_image(session, link, name, folder):
    async with session.get(link) as response:
        img_data = await response.read()
        with open(os.path.join(folder, name), 'wb') as handler:
            handler.write(img_data)

async def scrape_manhwa(url):
    title = ''
    if url[-1] == '/':
        title = url.rsplit('/', 1)[0].rsplit('/', 1)[1]
    else:
        title = url.rsplit('/', 1)[-1]
    title = title.replace('-', ' ')
    print("[*] Scraping: "+title)
    if not os.path.exists('./'+title):
        os.makedirs('./'+title)
        os.makedirs('./'+title+'/imgs')
        os.makedirs('./'+title+'/pdf')
    
    print("Fetching HTML...")
    # Bypass SSL certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url) as response:
            if response.status == 200:
                print("Parsing HTML...")
                soup = BeautifulSoup(await response.text(), 'html.parser')
                print("Extracting image links...")
                eles = soup.find_all("img", {"class": "article_ed__img"})
                links = []
                for ele in eles:
                    if ele.has_attr('src'):
                        links.append(ele['src'])

                c = 0
                print("Starting the download...")
                images = []
                tasks = []
                for link in links:
                    c += 1
                    name = str(c) + '.jpg'
                    images.append(name)
                    task = download_image(session, link, name, title + '/imgs')
                    tasks.append(task)
                
                # Wait for all download tasks to complete
                for i, task in enumerate(asyncio.as_completed(tasks), 1):
                    await task
                    sys.stdout.write(f'\r{i} out of {len(links)} downloaded...')
                    sys.stdout.flush()

                print("\nConverting to pdf...")
                images_to_pdf(images, title + "/pdf/" + title + ".pdf", title)
                print("[+] " + title + " is done!\n")
            else:
                print(f"Failed to retrieve the webpage. Status code: {response.status}")
                exit(0)

def images_to_pdf(image_list, output_pdf, title):
    w, h = 700, 1000
    if len(sys.argv) == 6:
        w, h = int(sys.argv[4]), int(sys.argv[5])
    pdf = FPDF(orientation='P', unit='pt', format=(w, h))
    
    for image in image_list:
        pdf.add_page()
        pdf.image(title + '/imgs/' + image, x=0, y=0, w=0, h=0)
    
    pdf.output(output_pdf)

def detect_num_index(s):
    e = -1
    b = -1
    for i in reversed(range(len(s))):
        if s[i].isnumeric():
            e = i + 1
            while i >= 0 and s[i].isnumeric():
                i -= 1
            b = i + 1
            break
    if e >= len(s):
        return [s[:b], "/"]
    return [s[:b], s[e:]]

async def main():
    if len(sys.argv) > 3:
        start = int(sys.argv[2])
        stop = int(sys.argv[3])
        url = detect_num_index(sys.argv[1])
        while start <= stop:
            link = url[0] + str(start) + url[1]
            await scrape_manhwa(link)
            start += 1

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
