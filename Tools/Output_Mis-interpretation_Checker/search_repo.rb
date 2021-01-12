require 'octokit'
require 'set'
require 'net/http'
require 'uri'

# Provide authentication credentials
# Solution 1
# client = Octokit::Client.new(:login => 'user-name', :password => 'password')
# Solution 2
client = Octokit::Client.new(:access_token => "your-token")

keyword = "analyze_sentiment"
code_dir = "codes"

# Repository list
# format: repo_name \t url
file_input = File.open("repo_list_language.txt", "r")
# file_input = File.open("test.txt", "r")

# for each repository
file_input.readlines.each{ |item|
  tmp = item.split(' ')
  repo_name = tmp[0]
  url = tmp[1]
  # USERNAME/REPO
  constraint = url.sub("https://github.com/","")
  puts constraint

  file_log = File.open("python_apps.txt", "a")
  output_str = '=== '+ constraint + "\n"
  flag = false
  code_subdir = "codes/" + constraint.gsub('/', '-')  

  begin
    # more info: https://help.github.com/en/github/searching-for-information-on-github/searching-code
    results = client.search_code(keyword+' repo:'+constraint)
    # if found, then output it
    if results.total_count > 0 then
      # file_log.puts keyword + " " +results.total_count.to_s
      results.items.each { |file|
        file_url = file.html_url.to_s
        # filter out direclty include lib code
        if file_url.include? 'lib/python' and file_url.include? '/site-packages' then
          next
        end
        if file_url.include? 'language/tests/' and file_url.include? '/v1' then
          next
        end
        if file_url.include? 'courses/developingapps/python' then
          next
        end
        if file_url.include? 'cloud/gapic/language/v1' then
          next
        end
        if file_url.include? 'language/cloud-client/v1' then
          next
        end
        if file_url.include? 'lib/google/cloud/language' then
          next
        end
        if file_url.include? 'venv/Lib/site-packages' then
          next
        end
        if file_url.include? 'providers/google/cloud/' then
          next
        end
        if file_url.include? '/google/cloud/language_v1' then
          next
        end
        if file_url.include? 'python-docs-samples-master/language' then
          next
        end
        if file_url.include? 'language/generated-samples/v1' then
          next
        end
        if file_url.include? 'example_dags' then
          next
        end

        if file_url.include? '.py' then
          # file_log.puts file_url
          output_str = output_str + file_url + "\n"
          if not flag then
            flag = true
            if not File.directory?(code_subdir) then
              Dir.mkdir(code_subdir)
            end
          end
          file_name = file_url[(file_url.rindex("/")+1)..-1]
          file_download_url = file_url.gsub('blob/', '').gsub('github.com','raw.githubusercontent.com')
          uri = URI.parse(file_download_url)
          response = Net::HTTP.get_response(uri)
          file_code = File.open(code_subdir+"/"+file_name, "w")
          file_code.puts response.body.to_s
          file_code.close
        end

      }
      if flag then
        file_log.print output_str
      end
    end
  rescue
    print "Error"
  end

  file_log.close
  sleep(2)

}
file_input.close()
