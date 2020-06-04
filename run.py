from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import os
import json

# ----------------

timeout = 10
download_blacklist = ["Video", "Web Page"]

DEBUG_MODE = True

# ----------------

def wait_by_xpath(browser, timeout, path):
    try:
        WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, path)))
    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()
    time.sleep(0.5)

def expand_shadow_element(browser, element):
    shadow_root = browser.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root

def get_menu_button(browser):
    parent1 = browser.find_element_by_css_selector("div d2l-dropdown d2l-navigation-button-notification-icon")
    sr1 = expand_shadow_element(browser, parent1)
    parent2 = sr1.find_element_by_css_selector("d2l-navigation-button[text='Select a course...']")
    sr2 = expand_shadow_element(browser, parent2)
    return sr2.find_element_by_css_selector("button[title='Select a course...']")

def log_in(browser, link, timeout, username, password):
    browser.get(link)
    # Wait for log in page
    wait_by_xpath(browser, timeout, "//img[@class='logoImage']")

    user = browser.find_element_by_xpath("//input[@id='userNameInput']")
    user.send_keys(username)
    time.sleep(0.4)

    pas = browser.find_element_by_xpath("//input[@id='passwordInput']")
    pas.send_keys(password)
    time.sleep(0.4)

    login = browser.find_element_by_xpath("//span[@id='submitButton']")
    login.click()

def navigate_up_directory(iteration):
    cwd = os.getcwd()
    for i in range(iteration):
        os.chdir("..")
    return cwd

def make_directories(course_links):
    for course_id, (course_name, course_link) in course_links.items():
        if not os.path.isdir(os.path.join(os.curdir, 'Updated_materials')):
            os.mkdir(os.path.join(os.curdir, 'Updated_materials'))
        if not os.path.isdir(os.path.join(os.curdir, 'Updated_materials', course_name)):
            os.mkdir(os.path.join(os.curdir, 'Updated_materials', course_name))

def get_browser(absolute_download_path=None):
    # Don't wait for whole page to load
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"

    option = webdriver.ChromeOptions()
    option.add_argument("--incognito")
    if absolute_download_path:
        prefs = {
            "download.default_directory": absolute_download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        }
        option.add_experimental_option('prefs', prefs)
    return webdriver.Chrome(desired_capabilities=caps, executable_path='./userdata/chromedriver.exe', options=option)

# Save as chrome shortcut
def save_shortcut(save_path, item):
    with open(os.path.join(save_path, item['name'] + '.url'), 'w') as shortcut:
        shortcut.write("[InternetShortcut]\n")
        shortcut.write(f"URL={item['link']}")

# Download or else save as chrome shortcut
def download_item(browser, item, save_path, download_blacklist):
    if item['type'] in download_blacklist:
        save_shortcut(save_path, item)
        return

    browser.get(item['link'])
    wait_by_xpath(browser, timeout, f"//h1[text()='{item['name']}']")
    try:
        download = browser.find_element_by_xpath("//button[text()='Download']")
        download.click()
        time.sleep(1)
        wait_by_xpath(browser, 20, f"//h1[text()='{item['name']}']")
    except NoSuchElementException:
        save_shortcut(save_path, item)

# Gets the difference state dictionary from past state to present state of file listings
def get_difference_state(present_state, past_state):
    result_dict = {}
    for course_id, course_dict in present_state.items():
    
        # Check if the course has already been saved
        if course_id not in past_state.keys():
            result_dict[course_id] = course_dict
            continue
        
        # Check if the section title has already been saved
        past_course_dict = past_state[course_id]

        for section_title, item_list in course_dict.items():
            if section_title not in past_course_dict.keys():
                result_dict[course_id][section_title] = item_list
                continue

            # Check if the file name has already been saved
            past_item_list = past_course_dict[section_title]
            
            for item_dict in item_list:
                in_previous = False
                item_name = item_dict['name']

                for past_item_dict in past_item_list:
                    if past_item_dict['name'] == item_name:
                        in_previous = True

                if not in_previous:
                    if course_id not in result_dict.keys():
                        result_dict[course_id] = {}
                    if section_title not in result_dict[course_id].keys():
                        result_dict[course_id][section_title] = []
                    
                    result_dict[course_id][section_title].append(item_dict)
    return result_dict

# -------------- METHODS ABOVE --------------- #

if not DEBUG_MODE:
    navigate_up_directory(2)

browser = get_browser()
userdata_folder = os.path.join(os.curdir, 'userdata')

with open(os.path.join(userdata_folder, 'user.txt'), 'r') as f:
    text = f.read()
    username = text.split('\n')[0]
    password = text.split('\n')[1]

courses = []
with open(os.path.join(userdata_folder, 'courses.txt') , 'r') as f:
    text = f.read()
    for course in text.split('\n'):
        courses.append(course)

if 'state.json' in os.listdir(userdata_folder):
    past_state = json.load(open(os.path.join(userdata_folder, 'state.json'), 'r'))
    is_initial = False
else:
    is_initial = True

log_in(browser, "https://elearn.smu.edu.sg/d2l/lp/auth/saml/login", timeout, username, password)

# --------- Elearn Home --------- #

# Wait for elearn home page
wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")

menu_button = get_menu_button(browser)
menu_button.click()

# Wait for menu
wait_by_xpath(browser, timeout, "//nav//ul/li//a")
print(courses)

# Search for course IDs in menu
course_links = {}
for course in courses:
    course_button = browser.find_element_by_xpath(f"//ul/li/div/div/div/a[contains(text(),'{course}')]") 
    course_content_link = course_button.get_attribute('href')
    course_id = course_content_link.split('/')[-1]
    course_links[course_id] = (course, f"https://elearn.smu.edu.sg/d2l/le/content/{course_id}/Home")


# --------- Elearn individual courses --------- #

present_state = {}
for course_id, (course_name, course_link) in course_links.items():
    present_state[course_id] = {}
    browser.get(course_link)
    wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")
    
    # Switch to Table of Contents if not switched
    try:
        browser.find_element_by_xpath("//h1[contains(@class,'vui-heading-1') and contains(text(),'Table of Contents')]")
    except NoSuchElementException:
        table_contents = browser.find_element_by_xpath("//a/div/div/div/div/div/div[contains(text(),'Table of Contents')]")
        table_contents.click()
        wait_by_xpath(browser, timeout, "//h1[contains(@class,'vui-heading-1') and contains(text(),'Table of Contents')]")

    sections = browser.find_elements_by_xpath("//div[@class='d2l-placeholder']/div/div/ul/li[.//ul]")
    print(len(sections))

    # Get names and links of items in each section
    problem_sections = set()
    for section in sections:
        title = section.find_element_by_xpath(".//div/div/h2[contains(@class,'d2l-heading') and contains(@class,'vui-heading-4')]")
        present_state[course_id][title.text] = []

        list_items = section.find_elements_by_xpath(".//div/div/div/ul/li")
        for list_item in list_items:
            item = list_item.find_element_by_xpath(".//a[contains(@class,'d2l-link')]")
            link = item.get_attribute('href')
            try:
                item_type = list_item.find_element_by_xpath(".//a[contains(@class,'d2l-link')]/following-sibling::div[1]/div").text
            except NoSuchElementException:
                item_type = ''
            present_state[course_id][title.text].append({'name': item.text, 'link' : link, 'type': item_type})

            if "javascript" in link:
                problem_sections.add(title.text)
    
    # If links not found in Table of Contents, check on individual sections
    for problem_section_title in problem_sections:
        side_title = section.find_element_by_xpath(f"//a/div/div/div/div/div/div[contains(text(),'{problem_section_title}')]")
        side_title.click()
        wait_by_xpath(browser, timeout, f"//h1[contains(@class,'vui-heading-1') and contains(text(),'{problem_section_title}')]")
        present_state[course_id][problem_section_title] = []

        inner_items = browser.find_elements_by_xpath("//div[@class='d2l-placeholder']/div/div/ul//ul/li//a[contains(@class,'d2l-link')]")
        for inner_item in inner_items:
            link = inner_item.get_attribute('href')
            try:
                item_type = browser.find_element_by_xpath("//ul//ul/li//a[contains(@class,'d2l-link')]/following-sibling::div[1]/div").text
            except NoSuchElementException:
                item_type = ''
            present_state[course_id][problem_section_title].append({'name': inner_item.text, 'link' : link, 'type': item_type})

with open(os.path.join(userdata_folder, 'state.json'), 'w') as f:
    json.dump(present_state, f, indent = 4)

# Make directories for downloaded files if not exist
make_directories(course_links)
browser.quit()

# # --------- If this is not the first time --------- #
    
if not is_initial:
    # DIFFERENCE DICTIONARY
    difference_state = get_difference_state(present_state, past_state)
    # print(difference_state)
    for course_id, course_dict in difference_state.items():
        save_path = os.path.join(os.getcwd(), 'Updated_materials', course_links[course_id][0]) + os.path.sep

        browser = get_browser(save_path)
        log_in(browser, "https://elearn.smu.edu.sg/d2l/lp/auth/saml/login", timeout, username, password)
        wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")

        for section_title, item_list in course_dict.items():
            for item in item_list:
                download_item(browser, item, save_path, download_blacklist)
        
        # Display announcements
        browser.get(f"https://elearn.smu.edu.sg/d2l/home/{course_id}")