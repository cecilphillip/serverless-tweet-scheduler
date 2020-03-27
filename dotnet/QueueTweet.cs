
using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Microsoft.Azure.WebJobs.ServiceBus;
using Microsoft.Azure.ServiceBus;
using System.Text;
using LinqToTwitter;

namespace TweetScheduler
{
    public static class TweetSchedulerOperations
    {
        [FunctionName("QueueTweet")]
        public static async Task<IActionResult> QueueTweet(
            [HttpTrigger(AuthorizationLevel.Function, "POST")]HttpRequest req,
            [ServiceBus("scheduled-tweets", Connection = "ServiceBusConnection", EntityType = EntityType.Queue)]IAsyncCollector<Message> collector)
        {
            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();

            if (string.IsNullOrEmpty(requestBody.Trim()))
            {
                return new BadRequestResult();
            }

            // Create Service Bus message
            var scheduledTweet = JsonConvert.DeserializeObject<ScheduledTweet>(requestBody);
            var message = new Message(Encoding.UTF8.GetBytes(scheduledTweet.StatusUpdate))
            {
                MessageId = Guid.NewGuid().ToString("N"),
                ScheduledEnqueueTimeUtc = DateTime.UtcNow + TimeSpan.FromMinutes(scheduledTweet.MinutesFromNow)
            };

            // Add message to queue
            await collector.AddAsync(message);

            return new AcceptedResult();
        }

        [FunctionName("ProcessTweet")]
        public static async Task ProcessTweet(
            [ServiceBusTrigger("scheduled-tweets", Connection = "ServiceBusConnection")] Message scheduledTweet,
            ILogger log)
        {
            var auth = new SingleUserAuthorizer
            {
                CredentialStore = new SingleUserInMemoryCredentialStore
                {
                    ConsumerKey = Environment.GetEnvironmentVariable("TwitterAPIKey"),
                    ConsumerSecret = Environment.GetEnvironmentVariable("TwitterAPISecret"),
                    AccessToken = Environment.GetEnvironmentVariable("TwitterAccessToken"),
                    AccessTokenSecret = Environment.GetEnvironmentVariable("TwitterAccessTokenSecret")
                }
            };
            var twitterContext = new TwitterContext(auth);
            var tweetStatus = Encoding.UTF8.GetString(scheduledTweet.Body);
            try
            {
                await twitterContext.TweetAsync(tweetStatus);
            }
            catch (Exception ex)
            {
                log.LogError(ex, $"{nameof(twitterContext.TweetAsync)} failed");
            }
        }
    }
    public class ScheduledTweet
    {
        public string StatusUpdate { get; set; }
        public double MinutesFromNow { get; set; }
    }
}
