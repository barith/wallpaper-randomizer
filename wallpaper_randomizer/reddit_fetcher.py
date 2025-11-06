"""Reddit API interaction for fetching wallpaper posts."""

import praw
import random
from typing import List, Optional, Dict, Any


class RedditFetcher:
    """Fetch wallpaper posts from Reddit."""

    def __init__(self, credentials: Dict[str, str]):
        """Initialize Reddit API client.

        Args:
            credentials: Dict with client_id, client_secret, user_agent
        """
        self.reddit = praw.Reddit(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            user_agent=credentials['user_agent']
        )

    def fetch_image_posts(
        self,
        subreddit_name: str,
        sort: str = 'top',
        time_filter: str = 'month',
        limit: int = 100,
        filter_nsfw: bool = True
    ) -> List[praw.models.Submission]:
        """Fetch image posts from a subreddit.

        Args:
            subreddit_name: Name of the subreddit (without r/)
            sort: How to sort posts (hot, new, top, controversial, rising)
            time_filter: Time filter for top/controversial (hour, day, week, month, year, all)
            limit: Maximum number of posts to fetch
            filter_nsfw: Whether to filter out NSFW posts (default: True)

        Returns:
            List of submissions that are images
        """
        subreddit = self.reddit.subreddit(subreddit_name)

        # Get posts based on sort method
        if sort == 'hot':
            posts = subreddit.hot(limit=limit)
        elif sort == 'new':
            posts = subreddit.new(limit=limit)
        elif sort == 'top':
            posts = subreddit.top(time_filter=time_filter, limit=limit)
        elif sort == 'controversial':
            posts = subreddit.controversial(
                time_filter=time_filter, limit=limit)
        elif sort == 'rising':
            posts = subreddit.rising(limit=limit)
        else:
            raise ValueError(f"Invalid sort method: {sort}")

        # Filter for image posts
        image_posts = []
        nsfw_filtered_count = 0
        for post in posts:
            # Filter NSFW if requested
            if filter_nsfw and post.over_18:
                nsfw_filtered_count += 1
                continue

            if self._is_image_post(post):
                image_posts.append(post)

        if filter_nsfw and nsfw_filtered_count > 0:
            print(f"  Filtered out {nsfw_filtered_count} NSFW post(s)")

        return image_posts

    def _is_image_post(self, submission: praw.models.Submission) -> bool:
        """Check if a submission is an image post.

        Args:
            submission: Reddit submission to check

        Returns:
            True if submission contains an image
        """
        # Check if it's a direct image link
        if submission.url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            return True

        # Check if it's an imgur link (common for wallpapers)
        if 'imgur.com' in submission.url and not submission.url.endswith('/'):
            return True

        # Check if it's a Reddit hosted image
        if hasattr(submission, 'post_hint') and submission.post_hint == 'image':
            return True

        return False

    def get_random_wallpaper_url(
        self,
        subreddits: List[str],
        sort: str = 'top',
        time_filter: str = 'month',
        limit: int = 100,
        selection_mode: str = 'random',
        skip_count: int = 0,
        exclude_indices: set = None,
        filter_nsfw: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get a wallpaper URL from given subreddits.

        Args:
            subreddits: List of subreddit names
            sort: How to sort posts
            time_filter: Time filter for top/controversial
            limit: Number of posts to fetch per subreddit
            selection_mode: How to select wallpaper ('random' or 'first')
            skip_count: Number of posts to skip for 'first' mode (0-based)
            exclude_indices: Set of indices to exclude for 'random' mode
            filter_nsfw: Whether to filter out NSFW posts (default: True)

        Returns:
            Dict with 'url', 'title', 'subreddit', 'permalink' or None if no images found
        """
        if exclude_indices is None:
            exclude_indices = set()

        all_image_posts = []

        # Fetch from all subreddits
        for subreddit_name in subreddits:
            try:
                posts = self.fetch_image_posts(
                    subreddit_name,
                    sort=sort,
                    time_filter=time_filter,
                    limit=limit,
                    filter_nsfw=filter_nsfw
                )
                all_image_posts.extend(posts)
                print(f"Found {len(posts)} image posts in r/{subreddit_name}")
            except Exception as e:
                print(f"Warning: Could not fetch from r/{subreddit_name}: {e}")
                continue

        if not all_image_posts:
            print("No image posts found in any subreddit")
            return None

        # Select post based on selection mode
        if selection_mode == 'first':
            # Try sequential selection
            if skip_count >= len(all_image_posts):
                print(
                    f"Skip count {skip_count} exceeds available posts ({len(all_image_posts)})")
                return None
            selected_post = all_image_posts[skip_count]
            selected_index = skip_count
        else:
            # Random selection, excluding previously tried indices
            available_indices = [i for i in range(
                len(all_image_posts)) if i not in exclude_indices]
            if not available_indices:
                print("No more untried posts available")
                return None
            selected_index = random.choice(available_indices)
            selected_post = all_image_posts[selected_index]

        return {
            'url': selected_post.url,
            'title': selected_post.title,
            'subreddit': selected_post.subreddit.display_name,
            'permalink': f"https://reddit.com{selected_post.permalink}",
            'index': selected_index
        }
