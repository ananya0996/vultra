import os
import re
import requests

# List of GitHub project URLs for Java/Maven-based projects.
# (Conventional mapping: we download the pom.xml file into the "java_projects" folder.)
java_projects = [
    "https://github.com/ReactiveX/RxJava#rxjava-reactive-extensions-for-the-jvm",
    "https://github.com/elastic/elasticsearch",
    "https://github.com/square/retrofit",
    "https://github.com/square/okhttp",
    "https://github.com/spring-projects/spring-boot",
    "https://github.com/google/guava",
    "https://github.com/PhilJay/MPAndroidChart",
    "https://github.com/bumptech/glide",
    "https://github.com/spring-projects/spring-framework",
    "https://github.com/JakeWharton/butterknife",
    "https://github.com/airbnb/lottie-android",
    "https://github.com/square/leakcanary",
    "https://github.com/apache/incubator-dubbo",
    "https://github.com/zxing/zxing",
    "https://github.com/greenrobot/EventBus",
    "https://github.com/Blankj/AndroidUtilCode",
    "https://github.com/nostra13/Android-Universal-Image-Loader",
    "https://github.com/square/picasso",
    "https://github.com/skylot/jadx",
    "https://github.com/facebook/fresco",
    "https://github.com/netty/netty",
    "https://github.com/libgdx/libgdx",
    "https://github.com/Netflix/Hystrix",
    "https://github.com/alibaba/fastjson",
    "https://github.com/CymChad/BaseRecyclerViewAdapterHelper",
    "https://github.com/afollestad/material-dialogs",
    "https://github.com/chrisbanes/PhotoView",
    "https://github.com/Tencent/tinker",
    "https://github.com/lgvalle/Material-Animations",
    "https://github.com/nickbutcher/plaid",
    "https://github.com/jfeinstein10/SlidingMenu",
    "https://github.com/jenkinsci/jenkins",
    "https://github.com/google/ExoPlayer",
    "https://github.com/greenrobot/greenDAO",
    "https://github.com/realm/realm-java",
    "https://github.com/orhanobut/logger",
    "https://github.com/bazelbuild/bazel",
    "https://github.com/mybatis/mybatis-3",
    "https://github.com/square/dagger",
    "https://github.com/google/guice",
    "https://github.com/google/auto",
    "https://github.com/junit-team/junit4",
    "https://github.com/mockito/mockito",
    "https://github.com/square/javapoet",
    "https://github.com/OpenRefine/OpenRefine",
    "https://github.com/google/j2objc",
    "https://github.com/facebook/rebound",
    "https://github.com/scribejava/scribejava",
    "https://github.com/square/moshi",
    "https://github.com/socketio/socket.io-client-java",
]

# List of GitHub project URLs for Node.js (NPM)–based projects.
# (Conventional mapping: we download the package.json file into the "javascript_projects" folder.)
javascript_projects = [
    "https://github.com/freeCodeCamp/freeCodeCamp",
    "https://github.com/vuejs/vue",
    "https://github.com/facebook/react",
    "https://github.com/twbs/bootstrap",
    "https://github.com/trekhleb/javascript-algorithms",
    "https://github.com/airbnb/javascript",
    "https://github.com/facebook/react-native",
    "https://github.com/d3/d3",
    "https://github.com/facebook/create-react-app",
    "https://github.com/axios/axios",
    "https://github.com/30-seconds/30-seconds-of-code",
    "https://github.com/nodejs/node",
    "https://github.com/vercel/next.js",
    "https://github.com/mrdoob/three.js",
    "https://github.com/mui-org/material-ui",
    "https://github.com/goldbergyoni/nodebestpractices",
    "https://github.com/awesome-selfhosted/awesome-selfhosted",
    "https://github.com/FortAwesome/Font-Awesome",
    "https://github.com/yangshun/tech-interview-handbook",
    "https://github.com/ryanmcdermott/clean-code-javascript",
    "https://github.com/webpack/webpack",
    "https://github.com/angular/angular.js",
    "https://github.com/hakimel/reveal.js",
    "https://github.com/typicode/json-server",
    "https://github.com/atom/atom",
    "https://github.com/jquery/jquery",
    "https://github.com/chartjs/Chart.js",
    "https://github.com/expressjs/express",
    "https://github.com/adam-p/markdown-here",
    "https://github.com/h5bp/html5-boilerplate",
    "https://github.com/gatsbyjs/gatsby",
    "https://github.com/lodash/lodash",
    "https://github.com/resume/resume.github.com",
]

# Create directories if they don't exist.
os.makedirs("java_projects", exist_ok=True)
os.makedirs("javascript_projects", exist_ok=True)

# Function to extract owner and repo from a GitHub URL.
def parse_github_url(url):
    # Remove any trailing fragments (e.g. "#rxjava-reactive-extensions-for-the-jvm")
    url = url.split("#")[0].strip()
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if match:
        owner, repo = match.groups()
        # Remove a possible .git suffix if present
        repo = repo.replace(".git", "")
        return owner, repo
    else:
        return None, None

# Function to try to download a file from a given repository.
def download_dependency_file(owner, repo, filename, folder):
    # Try branch 'master' then 'main'
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            # Save the file
            file_path = os.path.join(folder, f"{repo}-{filename}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Downloaded {filename} from {owner}/{repo} (branch: {branch})")
            return True
    print(f"Could not find {filename} for {owner}/{repo}")
    return False

# Process Java/Maven projects.
# Convention: For Java projects, download pom.xml
for url in java_projects:
    owner, repo = parse_github_url(url)
    if owner and repo:
        download_dependency_file(owner, repo, "pom.xml", "java_projects")
    else:
        print(f"Could not parse URL: {url}")

# Process Node.js projects.
# Convention: For Node.js projects, download package.json
for url in javascript_projects:
    owner, repo = parse_github_url(url)
    if owner and repo:
        download_dependency_file(owner, repo, "package.json", "javascript_projects")
    else:
        print(f"Could not parse URL: {url}")
