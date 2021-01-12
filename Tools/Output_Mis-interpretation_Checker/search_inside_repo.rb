require 'octokit'
require 'set'
require 'net/http'
require 'uri'

# Provide authentication credentials
# Solution 1
# client = Octokit::Client.new(:login => 'user-name', :password => 'password')
# Solution 2
client = Octokit::Client.new(:access_token => "your-token")

keyword = ARGV[0]
constraint = ARGV[1]
code_dir = ARGV[2]

code_subdir = code_dir + "/" + constraint.gsub('/', '-')  
# puts code_subdir

begin
  results = client.search_code(keyword+' repo:'+constraint)
  if results.total_count > 0 then
    results.items.each { |file|
      file_url = file.html_url.to_s
      if file_url.include? 'vendor/google/cloud/videointelligence/src/' or file_url.include? 'vendor/google/videointelligence/src/v1'then
        # do nothing
      else
        if file_url.include? '.py' then
          file_name = file_url[(file_url.rindex("/")+1)..-1]
          if FileTest::exist?(code_subdir+"/"+'--'+keyword+'--'+file_name) then
            puts "Exists"
          else
            file_download_url = file_url.gsub('blob/', '').gsub('github.com','raw.githubusercontent.com')
            uri = URI.parse(file_download_url)
            response = Net::HTTP.get_response(uri)
            file_code = File.open(code_subdir+"/"+'--'+keyword+'--'+file_name, "w")
            file_code.puts response.body.to_s
            file_code.close
            puts code_subdir+"/"+'--'+keyword+'--'+file_name
          end
        end
      end
    }
  end
rescue
  print "Error"
end
