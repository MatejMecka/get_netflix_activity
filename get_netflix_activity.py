from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from configparser import ConfigParser
import time

# Variable that dictates whether output is displayed on the console
show_output = True


class NetflixRetreiver(object):

    """
    Class to retrieve and download user's activity history from Netflix
    """

    def __init__(self):
        self.username = ''
        self.password = ''
        self.profile_name = ''
        self.baseurl = ''

    def getActivity(self):
        """
        The main function that lets the user download their Netflix activity
        """
        self.getLoginInfo()
        self.loginNetflix()

    def getLoginInfo(self):
        # Initialising the parser
        userParser = ConfigParser()
        userParser.read('userconfig.ini')
        userParser.optionxform = str
        parsingDictionary = {"service": "NETFLIX"}

        # Required variables for filling in Netflix login form
        self.baseurl = userParser.get(parsingDictionary['service'], 'url')
        self.username = userParser.get(parsingDictionary['service'], 'username')
        self.password = userParser.get(parsingDictionary['service'], 'password')
        self.profile_name = userParser.get(parsingDictionary['service'], 'profile_name')

    def loginNetflix(self):
        if show_output:
            print('Logging into Netflix')
        # Initialising Chrome driver
        driver = webdriver.Chrome()
        driver.get(self.baseurl)
        mutliPageLogin = False

        # Clearing email textbox and typing in user's email
        driver.find_element_by_name('email').clear()
        driver.find_element_by_name('email').send_keys(self.username)

        # Clearing password textbox
        try:
            driver.find_element_by_name('password').clear()

            # It is a double page login. So we first need to click on "Next" and then send the password
        except:
            driver.find_element_by_class_name('login-button').click()
            mutliPageLogin = True

        time.sleep(1)

        if mutliPageLogin:
            driver.find_element_by_name('password').clear()

        # Typing in user's password
        driver.find_element_by_name('password').send_keys(self.password)

        # Sometimes Netflix displays the password in a drop-down menu, if that happens
        # this block of code hides the password
        try:
            driver.find_elements_by_link_text('Hide Password').click()
        except:
            pass

        # Clicking on submit button
        driver.find_element_by_class_name('login-button').click()

        # Wait for profiles page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'profile-icon')))

        # Obtain profiles and names
        profiles = driver.find_elements_by_class_name('profile-icon')
        profile_names = driver.find_elements_by_class_name('profile-name')

        # If profiles in empty, it means there is only one default profile on the account
        if profiles is not None:
            if show_output:
                print('Selecting Profile')
            # Iterate through names to check for a match with user's profile name
            for i in range(len(profiles)):
                try:
                    if profile_names[i].text == self.profile_name:
                        # Click profile image associated with name
                        profiles[i].click()
                    elif i == len(profiles):
                        print('Error: Your profile name (\'%s\') was not found.' % self.profile_name)
                        print('       Please check if you entered the correct profile name in \'userconfig.ini\'')
                        driver.close()
                except StaleElementReferenceException:
                    pass

        # Using the commented block of code below didn't work on some systems
        # So instead a new tab is opened for the 'viewing activity' page
        time.sleep(1)
        # driver.get('https://www.netflix.com/viewingactivity')
        # driver.execute_script('window.open(\'https://www.netflix.com/viewingactivity\',\'_blank\');')
        # driver.switch_to.window(driver.window_handles[-1])

        # Wait for browse page to load
        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'profile-icon')))
        if show_output:
            print('Navigating Site')

        # your_account = driver.find_element_by_link_text('Your Account')
        # hov = ActionChains(driver).move_to_element(profile_icon).move_to_element(your_account).click()
        # hov.perform()

        # Hover then click sometimes fails, so it runs until it works with a maximum of 3 attempts
        hov_profile = driver.find_element_by_class_name('profile-icon')
        error_count = 0
        while True:
            try:
                # On some systems the profile icon is displayed differently.
                # For this reason if the previous attempt doesn't work,
                # the program searches for a different item that will do the same thing when clicked as the profile-icon
                if error_count == 1:
                    hov_profile = driver.find_element_by_class_name('profile-name')
                elif error_count == 2:
                    hov_profile = driver.find_element_by_class_name('profile-arrow')
                elif error_count == 3:
                    hov_profile = driver.find_element_by_class_name('avatar')
                elif error_count == 4:
                    hov_profile = driver.find_element_by_class_name('profile-link')
                elif error_count == 5:
                    hov_profile = driver.find_element_by_class_name('account-dropdown-button')
                elif error_count == 6:
                    hov_profile = driver.find_element_by_class_name('account-menu-item')
                elif error_count == 7:
                    hov_profile = driver.find_element_by_class_name('current-profile')
                else:
                    print('Error: Program was unable to find profile picture. Please report this issue')
                    break

                # Attempt to move to profile icon
                hov = ActionChains(driver).move_to_element(hov_profile)
                hov.perform()

                # Click on 'Your Account' which appears from drop-down menu provoked in previous step
                driver.find_element_by_link_text('Your Account').click()

                # Navigate to page containing viewing activity
                driver.find_element_by_link_text('Viewing activity').click()
                break
            except:
                error_count += 1

        time.sleep(2)
        # Scroll to the bottom of the page
        original = len(driver.find_elements_by_class_name('retableRow'))
        while True:
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(2)
            newer = len(driver.find_elements_by_class_name('retableRow'))
            if newer == original:
                break
            else:
                original = newer

        if show_output:
            print('Writing activity to \'netflix_activity.txt\'')

        # Open output file
        file = open('netflix_activity.txt', 'w+')
        # For every item viewed, outputs date and title to output file
        for row in driver.find_elements_by_class_name('retableRow'):
            date_cell = row.find_elements_by_tag_name('div')[0]
            title_cell = row.find_elements_by_tag_name('div')[1]
            file.write(date_cell.text + ' - ' + title_cell.text + '\n')

        if show_output:
            print('Finishing')
        # Close output file
        file.close()
        driver.close()
        if show_output:
            print('Process finished')


def main():
    test = NetflixRetreiver()
    test.getActivity()

if __name__ == "__main__":
    main()