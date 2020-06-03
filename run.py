from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time

def wait_by_xpath(browser, timeout, path):
    try:
        WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, path)))
    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()
    time.sleep(0.4)

def expand_shadow_element(browser, element):
    shadow_root = browser.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root

def get_menu_button(browser):
    parent1 = browser.find_element_by_css_selector("div d2l-dropdown d2l-navigation-button-notification-icon")
    sr1 = expand_shadow_element(browser, parent1)
    parent2 = sr1.find_element_by_css_selector("d2l-navigation-button[text='Select a course...']")
    sr2 = expand_shadow_element(browser, parent2)
    return sr2.find_element_by_css_selector("button[title='Select a course...']")

# --------------

option = webdriver.ChromeOptions()
option.add_argument("--incognito")

browser = webdriver.Chrome(executable_path='chromedriver.exe', options=option)

LINK = "https://elearn.smu.edu.sg/d2l/lp/auth/saml/login"
timeout = 10

# --------- Login Page --------- #

browser.get(LINK)

# Wait for log in page
wait_by_xpath(browser, timeout, "//img[@class='logoImage']")

with open('user.txt', 'r') as f:
    text = f.read()
    username = text.split('\n')[0]
    password = text.split('\n')[1]

courses = []
with open('courses.txt', 'r') as f:
    text = f.read()
    for course in text.split('\n'):
        courses.append(course)

user = browser.find_element_by_xpath("//input[@id='userNameInput']")
user.send_keys(username)
time.sleep(0.4)

pas = browser.find_element_by_xpath("//input[@id='passwordInput']")
pas.send_keys(password)
time.sleep(0.4)

login = browser.find_element_by_xpath("//span[@id='submitButton']")
login.click()

# --------- Elearn Home --------- #

# Wait for elearn home page
wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")

menu_button = get_menu_button(browser)
menu_button.click()

# Wait for menu
wait_by_xpath(browser, timeout, "//div/span/d2l-button-icon[@icon='tier1:pin-hollow']")
print(courses)

# Search for course IDs in menu
course_links = []
for course in courses:
    course_button = browser.find_element_by_xpath(f"//ul/li/div/div/div/a[contains(text(),'{course}')]") 
    course_content_link = course_button.get_attribute('href')
    course_id = course_content_link.split('/')[-1]
    course_links.append((course_id, f"https://elearn.smu.edu.sg/d2l/le/content/{course_id}/Home"))


# --------- Elearn individual courses --------- #

present_state = {}
for course_id, course_link in course_links:
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

        items = section.find_elements_by_xpath(".//div/div/div/ul/li")
        for item in items:
            item = item.find_element_by_xpath(".//a[contains(@class,'d2l-link')]")
            link = item.get_attribute('href')
            present_state[course_id][title.text].append({'name': item.text, 'link' : link})
            if "javascript" in link:
                problem_sections.add(title.text)

    # If links not found in Table of Contents, check on individual sections
    for problem_section_title in problem_sections:
        side_title = section.find_element_by_xpath(f"//a/div/div/div/div/div/div[contains(text(),'{problem_section_title}')]")
        side_title.click()
        wait_by_xpath(browser, timeout, f"//h1[contains(@class,'vui-heading-1') and contains(text(),'{problem_section_title}')]")
        present_state[course_id][problem_section_title] = []

        inner_items = browser.find_elements_by_xpath("//div[@class='d2l-placeholder']/div/div/ul//ul/li//a[@class='d2l-link']")
        for inner_item in inner_items:
            link = inner_item.get_attribute('href')
            present_state[course_id][problem_section_title].append({'name': inner_item.text, 'link' : link})

    print(present_state)