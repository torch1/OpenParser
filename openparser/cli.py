from parse import *
import sys

def main():
    if len(sys.argv) is not 0:
        if len(sys.argv) >= 2:
            data = None
            if "--recursive" in sys.argv:
                data = recursive_parse(sys.argv[1], verbose=True)
            else:
                data = webpage_from_url(sys.argv[1]).parse()
            if "--json" in sys.argv:
                print json.dumps(data, indent=4)
            else:
                print "OpenParser (a Torch project) // licensed GPLv3"
                print "Parsed: " + sys.argv[1]
                if data['description']:
                    print "> " + data['description']
                print "========= LINKS ========="
                for link in data['links']:
                    print ' '*4 + link['name']
                    print ' '*8 + link['url']
                print
                print "===== SOCIAL MEDIA ====="
                for sites in data['social_media'].values():
                    for site in sites:
                        print ' '*4 + site['name']
                        if site['name'] != site['url']:
                            print ' '*8 + site['url']
                print
                print "===== TELEPHONES ====="
                for telephone in data['telephones']:
                    if telephone['extended']:
                        print ' '*4 + telephone['extended'].replace("\n", " / ")
                    print ' '*8 + telephone['number'].replace("\n", " / ")
                print
                print "===== EMAILS ====="
                for email in data['emails']:
                    print ' '*4 + email['extended'].replace("\n", " / ")
                    if email['address'] != email['extended']:
                        print ' '*8 + email['address'].replace("\n", " / ")
        else:
            print "please pass in a URL as the first argument!"

if __name__ == '__main__':
    main()
