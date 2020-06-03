from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time

def wait_by_xpath(browser, timeout, path):
    try:
        WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, path)))
    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()

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

browser.get(LINK)

timeout = 10

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
time.sleep(0.6)

pas = browser.find_element_by_xpath("//input[@id='passwordInput']")
pas.send_keys(password)
time.sleep(0.5)

login = browser.find_element_by_xpath("//span[@id='submitButton']")
login.click()
time.sleep(0.5)

# Wait for elearn home page
wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")
time.sleep(0.5)

menu_button = get_menu_button(browser)
menu_button.click()

# Wait for menu
wait_by_xpath(browser, timeout, "//div/span/d2l-button-icon[@icon='tier1:pin-hollow']")
time.sleep(0.5)
print(courses)

course_links = []
for course in courses:
    course_button = browser.find_element_by_xpath(f"//ul/li/div/div/div/a[contains(text(),'{course}')]") 
    course_content_link = course_button.get_attribute('href')
    course_id = course_content_link.split('/')[-1]
    course_links.append((course_id, f"https://elearn.smu.edu.sg/d2l/le/content/{course_id}/Home"))

present_state = {}
for course_id, course_link in course_links:
    present_state[course_id] = {}
    browser.get(course_link)
    wait_by_xpath(browser, timeout, "//d2l-navigation-main-footer/div[@slot='main']")
    sections = browser.find_elements_by_xpath("//div[@class='d2l-placeholder']/div/div/ul/li[.//ul]")
    print(len(sections))

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

print(present_state)
print(problem_sections)